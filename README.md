# Lignex stain-shade posters: daily Instagram posting

20 posters (one per water-based stain shade) in `posters/`, queued in `posts_queue.json`.
A GitHub Actions job posts the next pending one every day at 7:00 PM India time.

## Files
| Path | What it is |
|---|---|
| `posters/01-...jpg` to `20-...jpg` | The 20 finished posters, 1080x1350 JPEG |
| `posts_queue.json` | Order, caption and image URL for each post, plus status |
| `run_agent.py`, `publish_instagram.py`, `queue_manager.py` | The posting code |
| `.github/workflows/scheduled-post.yml` | The 7:00 PM daily schedule (13:30 UTC) |
| `tools/shades.json` | Shade names, woods, articles, phone number. Edit, then re-run the two tools below |
| `tools/make_posters.py` | Re-draws all posters from `shades.json` |
| `tools/build_queue.py` | Re-builds `posts_queue.json` (captions and image URLs) |

## One-time setup
1. Push this folder to GitHub. Make the repo **public** (Instagram has to download the images
   from a public link; `.env` is ignored by git and your tokens live in GitHub Secrets, not in the repo).
2. Repo > Settings > Secrets and variables > Actions: add `IG_ACCESS_TOKEN` and `IG_USER_ID`.
3. Repo > Settings > Actions > General > Workflow permissions: "Read and write permissions".
4. Actions tab > "Daily Instagram Post" > Run workflow, to post poster 1 now as a test.

## Good to know
- After poster 20 the job finds nothing pending and exits quietly. Add more entries to continue.
- The Instagram token lasts 60 days. Generate a new one in the Meta dashboard before it expires
  and update the `IG_ACCESS_TOKEN` secret.
- Scheduled GitHub runs can start a few minutes after 7:00 PM.
