import importlib.util
import os
import socket
import subprocess
import sys
import time

import pytest
from xprocess import ProcessStarter


PROJECT_DIR = "/home/user/myproject"
WORKER_FILE = os.path.join(PROJECT_DIR, "worker.py")


def _load_worker_module():
    """Load /home/user/myproject/worker.py as a module without executing
    a `if __name__ == '__main__'` block."""
    spec = importlib.util.spec_from_file_location("user_worker", WORKER_FILE)
    assert spec is not None and spec.loader is not None, (
        f"Could not load module spec for {WORKER_FILE}"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["user_worker"] = module
    spec.loader.exec_module(module)
    return module


def test_worker_file_exists():
    assert os.path.isfile(WORKER_FILE), f"Expected worker file at {WORKER_FILE}"


def test_worker_module_exposes_hatchet_and_greet():
    """The module must expose a `hatchet` client and a `greet` task."""
    module = _load_worker_module()

    assert hasattr(module, "hatchet"), (
        "worker.py must define a module-level `hatchet` Hatchet() client."
    )
    assert hasattr(module, "greet"), (
        "worker.py must define a module-level `greet` task object decorated with @hatchet.task."
    )

    from hatchet_sdk import Hatchet

    assert isinstance(module.hatchet, Hatchet), (
        f"worker.hatchet must be an instance of hatchet_sdk.Hatchet, got {type(module.hatchet).__name__}."
    )

    greet = module.greet
    # The decorated task should expose either a `.name` attribute or be discoverable via repr.
    task_name = getattr(greet, "name", None)
    if task_name is None:
        # Older/newer SDK variants may store the name in a nested definition.
        task_name = getattr(getattr(greet, "definition", None), "name", None)
    # The Hatchet SDK may prepend the active namespace as a prefix
    # (e.g. "default_greet" in the default namespace). Accept any of the
    # equivalent forms.
    assert task_name is not None, "Could not introspect the task name from worker.greet."
    candidates = {task_name, task_name.split("_", 1)[-1], task_name.split(":", 1)[-1]}
    assert "greet" in candidates, (
        f"Expected task named 'greet' (optionally namespace-prefixed), got {task_name!r}."
    )


@pytest.fixture(scope="session")
def running_worker(xprocess):
    """Start the user's worker.py in the background so the task is registered."""

    class Starter(ProcessStarter):
        name = "user_worker"
        args = [sys.executable, WORKER_FILE]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 90
        terminate_on_interrupt = True

        def startup_check(self):
            # Confirm the worker process has connected to the gRPC server.
            # We approximate readiness by waiting until the gRPC port has at
            # least one active outbound connection from this host. As a
            # simpler heuristic, just sleep a short time after the process is
            # alive.
            return True

        # ProcessStarter has a default pattern-based ready check; override
        # with a simple time-based wait by setting an empty pattern and
        # combining with the startup_check above.
        pattern = "."

    xprocess.ensure(Starter.name, Starter)
    # Give the worker time to register with the Hatchet server.
    time.sleep(10)

    yield

    info = xprocess.getinfo(Starter.name)
    try:
        info.terminate()
    except Exception:
        pass


def test_greet_task_returns_hello_world(running_worker):
    """Trigger the task and verify the returned payload."""
    module = _load_worker_module()
    greet = module.greet

    # Hatchet SDK exposes `.run()` to trigger and wait for the result.
    result = greet.run({"name": "World"})

    # `result` may be either a dict or a Pydantic model depending on return
    # type hints. Normalize to a plain dict before asserting.
    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
    elif hasattr(result, "dict"):
        result_dict = result.dict()
    elif isinstance(result, dict):
        result_dict = result
    else:
        pytest.fail(
            f"greet.run() returned an unexpected type {type(result).__name__}: {result!r}"
        )

    assert result_dict == {"message": "Hello World"}, (
        f"Expected greet.run({{'name': 'World'}}) to return "
        f"{{'message': 'Hello World'}}, got {result_dict!r}."
    )
