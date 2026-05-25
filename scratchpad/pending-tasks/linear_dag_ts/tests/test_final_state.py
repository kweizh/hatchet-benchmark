import json
import os
import re
import socket
import time

import pytest
import requests
from xprocess import ProcessStarter

PROJECT_DIR = "/home/user/myproject"
HATCHET_API = "http://localhost:8888"
HATCHET_GRPC_PORT = 7077
WORKFLOW_NAME = "pipeline"
HATCHET_ENV_FILE = "/etc/hatchet.env"


def _load_hatchet_env_into_process() -> None:
    """Populate `os.environ` with the values written to /etc/hatchet.env by the
    container's startup script, so the Python SDK and any direct REST calls have
    real authentication credentials regardless of how pytest was invoked."""
    if not os.path.isfile(HATCHET_ENV_FILE):
        return
    pattern = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]+)=(.*)$")
    with open(HATCHET_ENV_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            match = pattern.match(line)
            if not match:
                continue
            key, value = match.group(1), match.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


_load_hatchet_env_into_process()


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _get_tenant_id() -> str:
    """Resolve the active Hatchet tenant id from environment or REST API."""
    explicit = os.environ.get("HATCHET_CLIENT_TENANT_ID")
    if explicit:
        return explicit
    # Fall back to the well-known default tenant id used by hatchet-lite quickstart.
    return "707d0855-80ab-4e1f-a156-f1c4546cbf52"


def _workflow_is_registered(tenant_id: str, token: str) -> bool:
    """Return True if a workflow named `pipeline` is registered with the engine."""
    try:
        resp = requests.get(
            f"{HATCHET_API}/api/v1/tenants/{tenant_id}/workflows",
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=5,
        )
    except requests.RequestException:
        return False
    if resp.status_code != 200:
        return False
    try:
        payload = resp.json()
    except ValueError:
        return False
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return False
    for row in rows:
        if isinstance(row, dict) and row.get("name") == WORKFLOW_NAME:
            return True
    return False


@pytest.fixture(scope="session")
def start_worker(xprocess):
    """Start the executor's TypeScript worker as a background process."""

    class Starter(ProcessStarter):
        name = "ts_worker_dag"
        args = ["npx", "ts-node", "worker.ts"]
        env = os.environ.copy()
        popen_kwargs = {
            "cwd": PROJECT_DIR,
            "text": True,
        }
        timeout = 240
        terminate_on_interrupt = True

        def startup_check(self):
            # The TS SDK opens a gRPC connection to the engine when the worker
            # starts and registers its workflow definitions. We consider the
            # worker "ready" once the `pipeline` workflow is visible via the
            # Hatchet REST API.
            tenant_id = _get_tenant_id()
            token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
            return _workflow_is_registered(tenant_id, token)

    xprocess.ensure(Starter.name, Starter)

    yield

    info = xprocess.getinfo(Starter.name)
    info.terminate()


def _extract_run_id(details) -> str:
    """Extract the workflow run external id from a V1WorkflowRunDetails response."""
    run = getattr(details, "run", None)
    if run is not None:
        meta = getattr(run, "metadata", None)
        if meta is not None:
            rid = getattr(meta, "id", None) or getattr(meta, "external_id", None)
            if rid:
                return str(rid)
    try:
        dumped = details.model_dump()
    except AttributeError:
        dumped = json.loads(
            json.dumps(details, default=lambda o: getattr(o, "__dict__", str(o)))
        )
    if isinstance(dumped, dict):
        run = dumped.get("run") or {}
        if isinstance(run, dict):
            meta = run.get("metadata") or {}
            if isinstance(meta, dict):
                rid = meta.get("id") or meta.get("external_id")
                if rid:
                    return str(rid)
        meta = dumped.get("metadata") or {}
        if isinstance(meta, dict):
            rid = meta.get("id") or meta.get("external_id")
            if rid:
                return str(rid)
    raise AssertionError(
        f"Could not determine workflow run id from create response: {details!r}"
    )


def _extract_output(details) -> dict:
    """Best-effort extraction of the workflow output from V1WorkflowRunDetails."""
    run = getattr(details, "run", None)
    if run is not None:
        output = getattr(run, "output", None)
        if isinstance(output, dict):
            return output
    try:
        dumped = details.model_dump()
    except AttributeError:
        dumped = json.loads(
            json.dumps(details, default=lambda o: getattr(o, "__dict__", str(o)))
        )
    if isinstance(dumped, dict):
        run = dumped.get("run") or {}
        if isinstance(run, dict):
            output = run.get("output")
            if isinstance(output, dict):
                return output
    return {}


def _run_workflow_and_get_task_outputs(
    input_payload: dict, timeout: float = 120.0
) -> dict:
    """Trigger the workflow via the Python SDK and return a mapping of
    `{task_name: output_dict}` for each task in the DAG run."""
    from hatchet_sdk import Hatchet

    hatchet = Hatchet()
    details = hatchet.runs.create(workflow_name=WORKFLOW_NAME, input=input_payload)
    run_id = _extract_run_id(details)

    # The synchronous `create` call may already include the final output for
    # quick runs, but we still poll defensively until a terminal status.
    deadline = time.time() + timeout
    terminal = False
    last_status = "UNKNOWN"
    while time.time() < deadline:
        try:
            status = hatchet.runs.get_status(workflow_run_id=run_id)
        except Exception:
            status = None
        last_status = str(status or "")
        upper = last_status.upper()
        if any(token in upper for token in ("SUCCEED", "COMPLETED", "COMPLETE")):
            terminal = True
            break
        if any(token in upper for token in ("FAIL", "CANCEL")):
            raise AssertionError(
                f"Workflow run {run_id} terminated with status {last_status}."
            )
        time.sleep(1.0)
    if not terminal:
        raise AssertionError(
            f"Workflow run {run_id} did not complete within {timeout}s "
            f"(last status: {last_status})."
        )

    # Fetch full run details: this includes a `tasks` list where each entry
    # carries the per-task `action_id` (formatted as `<workflow>:<task_name>`)
    # and the deserialized `output` dict.
    full = hatchet.runs.get(workflow_run_id=run_id)
    try:
        full_data = full.model_dump()
    except AttributeError:
        full_data = json.loads(
            json.dumps(full, default=lambda o: getattr(o, "__dict__", str(o)))
        )

    task_outputs: dict = {}
    tasks = full_data.get("tasks") if isinstance(full_data, dict) else None
    if isinstance(tasks, list):
        for task in tasks:
            if not isinstance(task, dict):
                continue
            action_id = task.get("action_id") or ""
            display_name = task.get("display_name") or ""
            output = task.get("output")
            if not isinstance(output, dict):
                continue
            # action_id is `<workflow>:<task_name>`; display_name is `<task>-<ts>`.
            name = None
            if ":" in action_id:
                name = action_id.split(":", 1)[1]
            elif "-" in display_name:
                # Best-effort fallback: strip the timestamp suffix.
                name = display_name.rsplit("-", 1)[0]
            if name:
                task_outputs[name] = output

    return task_outputs


def test_hatchet_engine_ports_open():
    assert _port_open("localhost", 8888), "Hatchet API port 8888 must be reachable."
    assert _port_open("localhost", HATCHET_GRPC_PORT), (
        f"Hatchet gRPC port {HATCHET_GRPC_PORT} must be reachable."
    )


def test_project_has_worker_ts():
    worker_path = os.path.join(PROJECT_DIR, "worker.ts")
    assert os.path.isfile(worker_path), (
        f"Expected worker entrypoint at {worker_path}. The executor must create worker.ts."
    )


def test_project_has_package_json_with_ts_sdk():
    pkg_path = os.path.join(PROJECT_DIR, "package.json")
    assert os.path.isfile(pkg_path), f"Expected package.json at {pkg_path}."
    with open(pkg_path, "r", encoding="utf-8") as fh:
        pkg = json.load(fh)
    deps = {}
    for key in ("dependencies", "devDependencies"):
        if isinstance(pkg.get(key), dict):
            deps.update(pkg[key])
    assert "@hatchet-dev/typescript-sdk" in deps, (
        "package.json must declare '@hatchet-dev/typescript-sdk' as a dependency."
    )


def test_node_modules_installed():
    assert os.path.isdir(os.path.join(PROJECT_DIR, "node_modules")), (
        "Node dependencies must be installed (run 'npm install' before verification)."
    )


def test_pipeline_workflow_registered(start_worker):
    """The TS worker must register the `pipeline` workflow with the engine."""
    tenant_id = _get_tenant_id()
    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    resp = requests.get(
        f"{HATCHET_API}/api/v1/tenants/{tenant_id}/workflows",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        timeout=10,
    )
    assert resp.status_code == 200, (
        f"Expected 200 from workflows listing endpoint, got {resp.status_code}: {resp.text}"
    )
    payload = resp.json()
    rows = payload.get("rows") if isinstance(payload, dict) else None
    assert rows, f"No workflows reported by the Hatchet API: {payload!r}"
    names = [row.get("name") for row in rows if isinstance(row, dict)]
    assert WORKFLOW_NAME in names, (
        f"Expected a workflow named '{WORKFLOW_NAME}' to be registered, got names: {names}"
    )


def test_pipeline_final_output_is_hello_world(start_worker):
    """The full DAG must produce {'final': 'HELLO WORLD'} from step3."""
    task_outputs = _run_workflow_and_get_task_outputs({})
    assert "step3" in task_outputs, (
        f"Expected per-task outputs to contain 'step3', got task names: "
        f"{sorted(task_outputs.keys())!r}"
    )
    assert task_outputs["step3"] == {"final": "HELLO WORLD"}, (
        f"Expected step3 output to be {{'final': 'HELLO WORLD'}}, got: "
        f"{task_outputs['step3']!r} (all task outputs: {task_outputs!r})"
    )


def test_pipeline_intermediate_task_outputs(start_worker):
    """Verify that step1 produced data='hello' and step2 produced msg='hello world'."""
    task_outputs = _run_workflow_and_get_task_outputs({})
    assert task_outputs.get("step1", {}).get("data") == "hello", (
        f"Expected step1 output to contain {{'data': 'hello'}}, got: "
        f"{task_outputs.get('step1')!r} (all task outputs: {task_outputs!r})"
    )
    assert task_outputs.get("step2", {}).get("msg") == "hello world", (
        f"Expected step2 output to contain {{'msg': 'hello world'}}, got: "
        f"{task_outputs.get('step2')!r} (all task outputs: {task_outputs!r})"
    )


def test_pipeline_real_execution_repeatable(start_worker):
    """Re-trigger the workflow to confirm real (non-mocked) execution end to end."""
    task_outputs = _run_workflow_and_get_task_outputs({})
    assert task_outputs.get("step3", {}).get("final") == "HELLO WORLD", (
        "Expected the TypeScript worker to produce the DAG result on a second run, "
        "confirming the verifier is calling the real running worker. Got: "
        f"{task_outputs!r}"
    )
