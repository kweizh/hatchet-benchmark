import importlib.util
import os
import sys
import time

import pytest
import requests
from xprocess import ProcessStarter


PROJECT_DIR = "/home/user/myproject"
WORKER_FILE = os.path.join(PROJECT_DIR, "worker.py")
EXPECTED_WORKER_NAME = "slot-worker"
EXPECTED_SLOT_LIMIT = 5


def _worker_name_matches(api_name, expected=EXPECTED_WORKER_NAME):
    """Return True if a worker name reported by the Hatchet REST API matches
    the user's requested worker name, allowing the SDK to prepend a default
    namespace (e.g. ``default_slot-worker`` is accepted for ``slot-worker``)."""
    if not isinstance(api_name, str):
        return False
    if api_name == expected:
        return True
    # The Python SDK prefixes the configured namespace with an underscore
    # separator (e.g. ``default_<name>``). Strip any single namespace prefix.
    if "_" in api_name and api_name.split("_", 1)[1] == expected:
        return True
    # Some older versions used a colon separator.
    if ":" in api_name and api_name.split(":", 1)[1] == expected:
        return True
    return False


def _load_worker_module():
    """Load /home/user/myproject/worker.py as a module without executing its
    `if __name__ == '__main__'` block."""
    spec = importlib.util.spec_from_file_location("user_worker", WORKER_FILE)
    assert spec is not None and spec.loader is not None, (
        f"Could not load module spec for {WORKER_FILE}"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["user_worker"] = module
    spec.loader.exec_module(module)
    return module


def _server_url():
    url = os.environ.get("HATCHET_CLIENT_SERVER_URL", "").rstrip("/")
    assert url, "HATCHET_CLIENT_SERVER_URL environment variable is not set."
    return url


def _tenant_id():
    tenant = os.environ.get("HATCHET_CLIENT_TENANT_ID", "")
    assert tenant, "HATCHET_CLIENT_TENANT_ID environment variable is not set."
    return tenant


def _api_token():
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token, "HATCHET_CLIENT_TOKEN environment variable is not set."
    return token


def _list_workers():
    url = f"{_server_url()}/api/v1/tenants/{_tenant_id()}/worker"
    headers = {"Authorization": f"Bearer {_api_token()}"}
    resp = requests.get(url, headers=headers, timeout=30)
    assert resp.status_code == 200, (
        f"GET {url} returned status {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    rows = data.get("rows", data)
    assert isinstance(rows, list), (
        f"Unexpected workers response shape, expected a list under 'rows': {data!r}"
    )
    return rows


def _extract_slot_limit(worker):
    """Pull the standard slot limit out of a worker payload, trying the
    several shapes the Hatchet REST API has used over time."""
    # 1. Newer engines expose top-level `maxRuns`.
    if isinstance(worker.get("maxRuns"), int):
        return worker["maxRuns"]
    # 2. Some versions report `slots` as an integer (not the SemaphoreSlots
    #    array). Only treat it as the limit when it is an int.
    if isinstance(worker.get("slots"), int):
        return worker["slots"]
    # 3. Newest engines expose `slotConfig` mapping slot_type -> {limit, ...}.
    slot_config = worker.get("slotConfig")
    if isinstance(slot_config, dict) and slot_config:
        # Prefer an entry that looks like the standard pool.
        candidates = []
        for key, value in slot_config.items():
            if not isinstance(value, dict):
                continue
            limit = value.get("limit")
            if not isinstance(limit, int):
                continue
            normalized_key = str(key).upper()
            score = 0
            if "STANDARD" in normalized_key:
                score = 2
            elif "DURABLE" in normalized_key:
                score = -1
            candidates.append((score, limit))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
    return None


def test_worker_file_exists():
    assert os.path.isfile(WORKER_FILE), f"Expected worker file at {WORKER_FILE}"


def test_worker_module_exposes_hatchet_and_noop():
    """The module must expose a `hatchet` client and a `noop` task."""
    module = _load_worker_module()

    assert hasattr(module, "hatchet"), (
        "worker.py must define a module-level `hatchet` Hatchet() client."
    )
    assert hasattr(module, "noop"), (
        "worker.py must define a module-level `noop` task object decorated with @hatchet.task."
    )

    from hatchet_sdk import Hatchet

    assert isinstance(module.hatchet, Hatchet), (
        f"worker.hatchet must be an instance of hatchet_sdk.Hatchet, got {type(module.hatchet).__name__}."
    )

    noop = module.noop
    task_name = getattr(noop, "name", None)
    if task_name is None:
        task_name = getattr(getattr(noop, "definition", None), "name", None)
    assert task_name is not None, "Could not introspect the task name from worker.noop."
    candidates = {task_name, task_name.split("_", 1)[-1], task_name.split(":", 1)[-1]}
    assert "noop" in candidates, (
        f"Expected task named 'noop' (optionally namespace-prefixed), got {task_name!r}."
    )


@pytest.fixture(scope="session")
def running_worker(xprocess):
    """Start the user's worker.py in the background so it registers with Hatchet."""

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
            return True

        pattern = "."

    xprocess.ensure(Starter.name, Starter)

    # Wait until the worker shows up in the REST API (with a generous timeout).
    deadline = time.time() + 60
    last_error = None
    while time.time() < deadline:
        try:
            workers = _list_workers()
            active = [
                w
                for w in workers
                if _worker_name_matches(w.get("name"))
                and w.get("status") == "ACTIVE"
            ]
            if active:
                break
            # Otherwise also accept any matching worker (the status may not
            # have flipped to ACTIVE yet on slower runs).
            any_match = [w for w in workers if _worker_name_matches(w.get("name"))]
            if any_match:
                # Give it a couple more seconds to flip to ACTIVE, then break.
                time.sleep(3)
                break
            time.sleep(2)
            continue
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    else:
        pytest.fail(
            f"Worker named {EXPECTED_WORKER_NAME!r} did not register with the Hatchet "
            f"server within 60s. Last error: {last_error!r}"
        )

    yield

    info = xprocess.getinfo(Starter.name)
    try:
        info.terminate()
    except Exception:
        pass


def test_worker_registered_with_slot_limit_5(running_worker):
    """The Hatchet REST API must report a worker named `slot-worker` with limit 5.

    Because the Hatchet engine keeps INACTIVE entries for previous worker
    sessions, we evaluate ONLY the most recently created ACTIVE worker
    matching the expected name. Stale entries from earlier runs are ignored.
    """
    workers = _list_workers()
    matches = [w for w in workers if _worker_name_matches(w.get("name"))]
    assert matches, (
        f"Expected to find a worker matching name {EXPECTED_WORKER_NAME!r} in the "
        f"Hatchet API (allowing a default namespace prefix), got names: "
        f"{[w.get('name') for w in workers]!r}"
    )

    active = [w for w in matches if w.get("status") == "ACTIVE"]
    assert active, (
        f"Expected at least one ACTIVE worker matching {EXPECTED_WORKER_NAME!r}; "
        f"found only statuses {[w.get('status') for w in matches]!r}. "
        "Did the worker start and connect to the Hatchet server?"
    )

    # If somehow multiple ACTIVE workers share the name, pick the most recent one.
    def _created_at(w):
        meta = w.get("metadata") or {}
        return meta.get("createdAt", "")

    active.sort(key=_created_at, reverse=True)
    most_recent = active[0]

    limit = _extract_slot_limit(most_recent)
    assert limit == EXPECTED_SLOT_LIMIT, (
        f"Expected the active worker matching {EXPECTED_WORKER_NAME!r} to advertise a "
        f"slot limit of {EXPECTED_SLOT_LIMIT}, got {limit!r} from payload {most_recent!r}."
    )


def test_noop_task_returns_ok_true(running_worker):
    """Trigger the noop task and verify the returned payload."""
    module = _load_worker_module()
    noop = module.noop

    result = noop.run({})

    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
    elif hasattr(result, "dict"):
        result_dict = result.dict()
    elif isinstance(result, dict):
        result_dict = result
    else:
        pytest.fail(
            f"noop.run({{}}) returned an unexpected type {type(result).__name__}: {result!r}"
        )

    assert result_dict == {"ok": True}, (
        f"Expected noop.run({{}}) to return {{'ok': True}}, got {result_dict!r}."
    )
