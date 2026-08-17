import os
import requests
import cloudinary
import cloudinary.uploader
from pathlib import Path

def load_env():
    env = Path("/root/Magbetai/.env")
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def publish_reel(video_path, caption):
    load_env()

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
    )

    video_path = Path(video_path)

    result = cloudinary.uploader.upload(
        str(video_path),
        folder="magbets_ai/reels",
        resource_type="video",
    )

    video_url = result["secure_url"]

    webhook_url = os.environ.get("MAKE_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("MAKE_WEBHOOK_URL missing")

    response = requests.post(
        webhook_url,
        data={
            "caption": caption,
            "filename": video_path.name,
            "video_url": video_url,
            "content_type": "reel",
        },
        timeout=90,
    )

    response.raise_for_status()

    print("REEL UPLOADED:", video_url)
    print("REEL SENT TO MAKE")
    return video_url

if __name__ == "__main__":
    folder = Path("/root/Magbetai/generated/runway_reels")
    files = list(folder.glob("*_FINAL.mp4"))

    if not files:
        raise RuntimeError("No FINAL reel found")

    latest = max(files, key=lambda p: p.stat().st_mtime)

    caption = "⚽ Latest football update from Magbets AI. Follow @magbets.ng for more."

    publish_reel(latest, caption)
