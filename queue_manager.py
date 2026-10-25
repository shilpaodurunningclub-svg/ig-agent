"""
Simple JSON content queue (posts_queue.json).

Entry: {"id", "topic", "caption" (optional), "image_url", "image_urls" (optional, 2-10 = carousel), "status"}
status is "pending" | "posted" | "failed" | "skipped". The agent always takes
the first "pending" entry, so posts go out in file order, one per run.
"""

import json
import os
from datetime import datetime, timezone

QUEUE_FILE = "posts_queue.json"


class QueueEmptyError(Exception):
    pass


def load_queue() -> list:
    if not os.path.exists(QUEUE_FILE):
        raise FileNotFoundError(f"{QUEUE_FILE} not found.")
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)


def save_queue(queue: list) -> None:
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")


def get_next_pending() -> dict:
    for entry in load_queue():
        if entry.get("status") == "pending":
            return entry
    raise QueueEmptyError("No pending posts left in the queue.")


def update_status(post_id: str, status: str, extra: dict = None) -> None:
    queue = load_queue()
    for entry in queue:
        if entry.get("id") == post_id:
            entry["status"] = status
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            if extra:
                entry.update(extra)
            break
    save_queue(queue)


def queue_summary() -> dict:
    counts = {}
    for entry in load_queue():
        s = entry.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


if __name__ == "__main__":
    print("Queue summary:", queue_summary())
    try:
        nxt = get_next_pending()
        print("Next pending:", nxt["id"], "-", nxt.get("topic"))
    except QueueEmptyError as e:
        print(e)
