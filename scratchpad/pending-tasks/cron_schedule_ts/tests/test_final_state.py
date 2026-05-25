import json
import os
import re
import subprocess
from datetime import datetime


HEARTBEAT_LOG = "/tmp/heartbeats.log"
PROJECT_DIR = "/home/user/myproject"
ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def test_heartbeat_log_exists():
    assert os.path.isfile(HEARTBEAT_LOG), (
        f"Expected heartbeat log file {HEARTBEAT_LOG} to exist after task completion."
    )


def test_heartbeat_log_contains_valid_iso_timestamp():
    with open(HEARTBEAT_LOG, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert lines, f"Heartbeat log {HEARTBEAT_LOG} is empty; expected at least one timestamp line."

    valid_lines = []
    for line in lines:
        if not ISO_REGEX.match(line):
            continue
        try:
            datetime.fromisoformat(line.replace("Z", "+00:00"))
        except ValueError:
            continue
        valid_lines.append(line)

    assert valid_lines, (
        f"Expected at least one valid ISO 8601 UTC timestamp line in {HEARTBEAT_LOG}, "
        f"but found none. Sample lines: {lines[:5]}"
    )


def test_cron_trigger_deleted_in_hatchet_cloud():
    run_id = _run_id()
    cron_name = f"hb-cron-ts-{run_id}"

    token = os.environ.get("HATCHET_CLIENT_TOKEN", "")
    assert token, "HATCHET_CLIENT_TOKEN environment variable must be set for verification."

    script = r"""
const { Hatchet } = require('@hatchet-dev/typescript-sdk');

(async () => {
  try {
    const hatchet = Hatchet.init();
    const crons = await hatchet.crons.list({});
    const rows = (crons && (crons.rows || crons.data || crons)) || [];
    const list = Array.isArray(rows) ? rows : [];
    const names = list
      .map((c) => (c && (c.name || (c.metadata && c.metadata.name))) || '')
      .filter(Boolean);
    process.stdout.write(JSON.stringify({ ok: true, names }));
  } catch (err) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(err && err.message || err) }));
  }
})();
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Failed to list Hatchet cron triggers via SDK. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )

    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise AssertionError(
            f"Could not parse Hatchet cron list output: {result.stdout!r}"
        ) from exc

    assert payload.get("ok"), (
        f"Hatchet SDK reported an error while listing crons: {payload.get('error')}"
    )

    names = payload.get("names", [])
    assert cron_name not in names, (
        f"Expected cron trigger {cron_name!r} to be deleted, but it is still present "
        f"in the Hatchet Cloud cron list: {names}"
    )
