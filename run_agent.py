"""
Posts the next pending item from posts_queue.json to Instagram.

If the entry has a "caption" it is used as written (no AI call). Otherwise a
caption is generated from the topic with generate_content.py.

Usage:
  python3 run_agent.py --from-queue                 # asks for confirmation first
  python3 run_agent.py --from-queue --no-approval   # used by the scheduled job
  python3 run_agent.py --topic "..." --image-url "https://..."   # one-off

Exit code is 1 when a publish fails, so the scheduled job shows as failed.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from publish_instagram import post_to_instagram, InstagramPublishError
from queue_manager import get_next_pending, update_status, QueueEmptyError

LOG_FILE = "post_log.json"


def log_post(entry: dict) -> None:
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
        f.write("\n")


def run(topic, image_url, caption=None, require_approval=True, post_id=None) -> bool:
    if not caption:
        from generate_content import generate_caption  # only needed when no caption is saved
        print(f"Generating caption for topic: {topic}")
        caption = generate_caption(topic)

    print("\n--- Caption ---")
    print(caption)
    print(f"Image: {image_url}")
    print("---------------\n")

    base = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "post_id": post_id, "topic": topic, "caption": caption, "image_url": image_url,
    }

    if require_approval:
        if input("Publish this post? [y/N]: ").strip().lower() != "y":
            print("Skipped. Nothing was published.")
            log_post({**base, "status": "skipped_by_user"})
            if post_id:
                update_status(post_id, "skipped")
            return True

    try:
        media_id = post_to_instagram(image_url, caption)
    except InstagramPublishError as e:
        print(f"Failed to publish: {e}")
        log_post({**base, "status": "failed", "error": str(e)})
        if post_id:
            update_status(post_id, "failed", {"error": str(e)})
        return False

    print(f"Published. Media ID: {media_id}")
    log_post({**base, "status": "published", "media_id": media_id})
    if post_id:
        update_status(post_id, "posted", {"media_id": media_id})
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram posting agent")
    parser.add_argument("--topic")
    parser.add_argument("--image-url")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--no-approval", action="store_true")
    args = parser.parse_args()

    if args.from_queue:
        try:
            entry = get_next_pending()
        except QueueEmptyError as e:
            print(e)
            sys.exit(0)
        ok = run(entry.get("topic", ""), entry["image_url"], entry.get("caption"),
                 require_approval=not args.no_approval, post_id=entry["id"])
    else:
        if not args.topic or not args.image_url:
            parser.error("--topic and --image-url are required unless using --from-queue")
        ok = run(args.topic, args.image_url, require_approval=not args.no_approval)

    sys.exit(0 if ok else 1)
