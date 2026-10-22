"""
Publishes an image post to Instagram through the Instagram API.

Flow (required by Instagram):
  1. Create a media container (POST image_url + caption)
  2. Poll the container until its status is FINISHED
  3. Publish the container (POST creation_id)

The token created under "Instagram API setup" in the Meta developer dashboard
is an Instagram User access token, which is used with graph.instagram.com.
If you ever switch to a Facebook Page token, set IG_GRAPH_HOST to
https://graph.facebook.com in .env.

Requirements:
  - Instagram Business/Creator account, added as an Instagram Tester on the app
  - Token with the instagram_business_content_publish permission
  - Image must be a JPEG at a PUBLIC url (Instagram fetches it server-side)
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_VERSION = "v21.0"
GRAPH_HOST = os.getenv("IG_GRAPH_HOST", "https://graph.instagram.com").rstrip("/")
BASE_URL = f"{GRAPH_HOST}/{GRAPH_API_VERSION}"

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")


class InstagramPublishError(Exception):
    pass


def _post(url, payload):
    resp = requests.post(url, data=payload, timeout=60)
    try:
        return resp.json()
    except ValueError:
        raise InstagramPublishError(f"Non-JSON response ({resp.status_code}): {resp.text[:300]}")


def create_media_container(image_url: str, caption: str) -> str:
    data = _post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        {"image_url": image_url, "caption": caption, "access_token": IG_ACCESS_TOKEN},
    )
    if "id" not in data:
        raise InstagramPublishError(f"Container creation failed: {data}")
    return data["id"]


def wait_until_ready(creation_id: str, max_attempts: int = 20, delay_seconds: int = 5) -> None:
    url = f"{BASE_URL}/{creation_id}"
    params = {"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
    for _ in range(max_attempts):
        data = requests.get(url, params=params, timeout=60).json()
        status = data.get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise InstagramPublishError(f"Container processing failed: {data}")
        time.sleep(delay_seconds)
    raise InstagramPublishError("Timed out waiting for container to be ready.")


def publish_container(creation_id: str) -> str:
    data = _post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        {"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
    )
    if "id" not in data:
        raise InstagramPublishError(f"Publish failed: {data}")
    return data["id"]


def post_to_instagram(image_url: str, caption: str) -> str:
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        raise InstagramPublishError("Missing IG_ACCESS_TOKEN or IG_USER_ID.")
    creation_id = create_media_container(image_url, caption)
    wait_until_ready(creation_id)
    return publish_container(creation_id)


def refresh_token() -> str:
    """Refresh the 60-day Instagram token (must be at least 24h old and not expired)."""
    resp = requests.get(
        f"{GRAPH_HOST}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": IG_ACCESS_TOKEN},
        timeout=60,
    ).json()
    if "access_token" not in resp:
        raise InstagramPublishError(f"Token refresh failed: {resp}")
    return resp["access_token"]


if __name__ == "__main__":
    print("Run run_agent.py to post. This module is imported by it.")
