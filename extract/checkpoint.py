"""
Checkpoint management for incremental pipeline runs.

The checkpoint is a small JSON file recording the timestamp through which
we've successfully processed matches. Each run reads it to know where to
start, and only updates it after successfully completing and saving new
data — never before. This means a failed or interrupted run leaves the
checkpoint untouched, so the next run safely retries the same window
instead of silently skipping unprocessed data.
"""
import json
import os
from datetime import datetime, timezone

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoint.json")

# The very first run has no prior checkpoint. This is the fallback start
# date — effectively "the beginning of what we care about." Adjust this
# if you want the initial backfill to reach further back.
DEFAULT_START = "2024-01-01T00:00:00Z"


def read_checkpoint() -> str:
    """Return the ISO timestamp of the last successful run, or the default."""
    if not os.path.exists(CHECKPOINT_PATH):
        return DEFAULT_START
    with open(CHECKPOINT_PATH, "r") as f:
        data = json.load(f)
    return data.get("last_successful_run_through", DEFAULT_START)


def write_checkpoint(new_timestamp: str) -> None:
    """
    Overwrite the checkpoint with a new timestamp.
    Only call this AFTER new data has been successfully written to disk.
    """
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump({
            "last_successful_run_through": new_timestamp,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)


if __name__ == "__main__":
    print("Current checkpoint:", read_checkpoint())