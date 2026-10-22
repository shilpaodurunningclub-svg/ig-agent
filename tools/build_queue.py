"""
Builds posts_queue.json from tools/shades.json and the posters/ folder.

Each entry carries its own ready-written caption, so the daily job needs no AI
call. Change GITHUB_USER / REPO / BRANCH below if the repo lives elsewhere.
The image URL must be PUBLIC (Instagram downloads it from its own servers), so
the repo must be public, or point IMAGE_BASE_URL at any other public host.

Usage (from the project root):  python3 tools/build_queue.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GITHUB_USER = "shilpaodurunningclub-svg"
REPO = "ig-agent"
BRANCH = "main"
IMAGE_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO}/{BRANCH}/posters"

HASHTAGS = (
    "#WoodStain #WaterBasedStain #WoodFinishing #FurnitureFinish #WoodenFurniture "
    "#InteriorDesign #LignexWoodfinishingStudio"
)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    cfg = json.loads((ROOT / "tools" / "shades.json").read_text())
    queue = []
    for i, s in enumerate(cfg["shades"], 1):
        fname = f"{i:02d}-{slug(s['name'])}.jpg"
        if not (ROOT / "posters" / fname).exists():
            raise SystemExit(f"Missing poster {fname}. Run tools/make_posters.py first.")
        caption = (
            f"{s['name']} water-based wood stain ({i}/{len(cfg['shades'])})\n\n"
            f"{s['look']}\n"
            f"Best on: {', '.join(s['best'])}.\n\n"
            "Water-based, low odour, fast drying.\n\n"
            f"{cfg['contact_line']} {cfg['contact_phone']}\n"
            f"{cfg['studio']}\n\n"
            f"{HASHTAGS}"
        )
        queue.append({
            "id": f"stain-{i:02d}",
            "topic": f"{s['name']} water-based wood stain",
            "caption": caption,
            "image_url": f"{IMAGE_BASE_URL}/{fname}",
            "status": "pending",
        })
    (ROOT / "posts_queue.json").write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote posts_queue.json with {len(queue)} posts")


if __name__ == "__main__":
    main()
