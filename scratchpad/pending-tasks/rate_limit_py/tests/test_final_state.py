import os
import re
from datetime import datetime, timezone

LOG_FILE = "/tmp/rate_log.txt"
EXPECTED_COUNT = 15
WINDOW_SECONDS = 60
WINDOW_LIMIT = 5
MIN_ELAPSED_SECONDS = 50

_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def _parse_iso_z(line: str) -> datetime:
    """Parse a UTC ISO-8601 timestamp ending in 'Z' into an aware datetime."""
    # datetime.fromisoformat does not accept the trailing 'Z' on Python <3.11,
    # so normalise it to '+00:00' before parsing.
    normalised = line[:-1] + "+00:00"
    return datetime.fromisoformat(normalised).astimezone(timezone.utc)


def _read_lines():
    assert os.path.isfile(LOG_FILE), (
        f"Expected rate-limit log file {LOG_FILE} to exist after the task completes."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        raw = f.read()
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def test_log_file_has_expected_line_count():
    lines = _read_lines()
    assert len(lines) == EXPECTED_COUNT, (
        f"Expected exactly {EXPECTED_COUNT} non-empty lines in {LOG_FILE}, "
        f"but found {len(lines)} lines. Content: {lines!r}"
    )


def test_log_lines_are_iso8601_utc_z():
    lines = _read_lines()
    for ln in lines:
        assert _ISO_RE.match(ln), (
            f"Line {ln!r} in {LOG_FILE} is not a valid UTC ISO 8601 timestamp "
            f"ending in 'Z' (expected e.g. '2025-05-25T12:34:56.789012Z')."
        )
        # And it must actually parse as a real datetime.
        try:
            _parse_iso_z(ln)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"Line {ln!r} in {LOG_FILE} could not be parsed as a UTC "
                f"datetime: {exc}"
            )


def test_total_elapsed_proves_rate_limiting():
    lines = _read_lines()
    timestamps = sorted(_parse_iso_z(ln) for ln in lines)
    elapsed = (timestamps[-1] - timestamps[0]).total_seconds()
    assert elapsed >= MIN_ELAPSED_SECONDS, (
        f"Expected the spread between the earliest and latest timestamp in "
        f"{LOG_FILE} to be at least {MIN_ELAPSED_SECONDS}s (proof that the "
        f"Hatchet static rate limit actually throttled execution), but the "
        f"observed spread was only {elapsed:.2f}s. Timestamps: "
        f"{[t.isoformat() for t in timestamps]}"
    )


def test_no_window_exceeds_rate_limit():
    lines = _read_lines()
    timestamps = sorted(_parse_iso_z(ln) for ln in lines)
    # For each timestamp t, count how many timestamps fall in [t, t + WINDOW_SECONDS].
    for i, t in enumerate(timestamps):
        count = 0
        for u in timestamps[i:]:
            if (u - t).total_seconds() <= WINDOW_SECONDS:
                count += 1
            else:
                break
        assert count <= WINDOW_LIMIT, (
            f"Found {count} timestamps within a {WINDOW_SECONDS}s window starting "
            f"at {t.isoformat()}, which exceeds the configured rate limit of "
            f"{WINDOW_LIMIT} per {WINDOW_SECONDS}s. Hatchet's static rate limit "
            f"does not appear to have been enforced. All timestamps: "
            f"{[ts.isoformat() for ts in timestamps]}"
        )
