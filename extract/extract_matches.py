"""
Extract new flagship VCT matches since the last successful run.

Pages backward through PandaScore's /valorant/matches/past endpoint
(most recent first), keeps only matches that are both (a) newer than our
last checkpoint and (b) classified as flagship VCT by vct_filters, and
writes them to a dated raw JSON file. The checkpoint is only advanced
after the write succeeds.
"""
import json
import os
from datetime import datetime, timezone

from pandascore_client import PandaScoreClient
from vct_filters import is_flagship_vct_serie, VCT_LEAGUE_ID
from checkpoint import read_checkpoint, write_checkpoint

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def extract_new_matches():
    checkpoint_ts = read_checkpoint()
    checkpoint_dt = parse_iso(checkpoint_ts)
    print(f"Checkpoint: fetching matches newer than {checkpoint_ts}")

    client = PandaScoreClient()
    new_matches = []
    newest_end_at_seen = checkpoint_ts
    page = 1
    reached_old_data = False

    while not reached_old_data:
        resp = client.get_matches_page(page=page, per_page=50, sort="-end_at")
        matches = resp.json()

        if not matches:
            print("No more pages available.")
            break

        for m in matches:
            end_at = m.get("end_at")
            if not end_at:
                continue  # some matches lack an end_at (e.g. forfeits) — skip safely

            match_dt = parse_iso(end_at)

            if match_dt <= checkpoint_dt:
                # We've paged back far enough to hit already-processed data.
                reached_old_data = True
                break

            serie_name = m.get("serie", {}).get("full_name", "")
            league_id = m.get("league", {}).get("id")
            if is_flagship_vct_serie(serie_name) and league_id == VCT_LEAGUE_ID:
                new_matches.append(m)
                if end_at > newest_end_at_seen:
                    newest_end_at_seen = end_at

        print(f"Page {page}: scanned {len(matches)} matches, kept {len(new_matches)} so far")
        page += 1

    if not new_matches:
        print("No new flagship VCT matches found. Nothing to write.")
        return

    os.makedirs(RAW_DIR, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(RAW_DIR, f"matches_incremental_{run_id}.json")

    with open(out_path, "w") as f:
        json.dump(new_matches, f, indent=2)
    print(f"Wrote {len(new_matches)} new matches to {out_path}")

    # Only advance the checkpoint now that the write above succeeded.
    write_checkpoint(newest_end_at_seen)
    print(f"Checkpoint advanced to {newest_end_at_seen}")


if __name__ == "__main__":
    extract_new_matches()