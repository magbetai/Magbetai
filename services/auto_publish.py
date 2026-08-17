from pathlib import Path
import json
import os
import random

import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv

from services.magbet_fixtures import get_today_fixtures
from services.graphics_v2 import create_tips_image, create_ai_news_image
from services.predictions import build_daily_tips
from services.trend_hunter import main as run_trend_hunter
from services.seo_generator import main as run_seo_generator
from services.video_creator import main as run_video_creator
from services.runway_reel_creator import main as run_runway_reel_creator
from services.reel_publish import publish_reel
from services.x_publish import post_to_x

PROJECT_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_DIR / "generated"

load_dotenv(PROJECT_DIR / ".env")

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def get_latest_caption() -> str:
    caption_files = sorted(
        GENERATED_DIR.glob("caption_*.txt"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if caption_files:
        return caption_files[0].read_text().strip()

    return (
        "Today's Magbets AI football predictions are ready.\n\n"
        "Play responsibly. 18+\n"
        "Visit magbets.ng"
    )


def main() -> None:
    if not MAKE_WEBHOOK_URL:
        raise RuntimeError("MAKE_WEBHOOK_URL is missing from .env")

    required_cloudinary = [
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    ]

    missing = [name for name in required_cloudinary if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing Cloudinary settings: " + ", ".join(missing)
        )

    fixtures = get_today_fixtures()
    tips = build_daily_tips(fixtures, limit=5)

    if not tips:
        print("WARNING: No suitable tips generated - skipping AI Tips for this run.")

    image_path = Path(create_tips_image(tips))
    caption = get_latest_caption()

    # === POST MAGBETS AI TIPS FIRST ===
    if tips:
        tips_caption = "🔥 MAGBETS AI FOOTBALL TIPS\n\n"
        for i, tip in enumerate(tips, 1):
            tips_caption += (
                f"{i}. {tip.get('home')} vs {tip.get('away')}\n"
                f"Pick: {tip.get('prediction')}\n"
                f"Confidence: {tip.get('confidence')}%\n\n"
            )

        tips_caption += "Bet responsibly. Visit magbets.ng\n#Magbets #FootballTips #BettingTips"

        tips_upload = cloudinary.uploader.upload(
            str(image_path),
            folder="magbets_ai",
            resource_type="image",
        )

        tips_url = tips_upload.get("secure_url")
        if not tips_url:
            raise RuntimeError("Cloudinary did not return tips image URL")

        with image_path.open("rb") as image_file:
            tips_response = requests.post(
                MAKE_WEBHOOK_URL,
                files={
                    "image": (
                        image_path.name,
                        image_file,
                        "image/jpeg",
                    )
                },
                data={
                    "filename": image_path.name,
                    "caption": tips_caption,
                    "image_url": tips_url,
                    "ab_variant": "TIPS",
                    "ab_headline": "MAGBETS AI FOOTBALL TIPS",
                },
                timeout=90,
            )

        tips_response.raise_for_status()

        print("MAGBETS AI TIPS SENT SUCCESSFULLY")
        print("TIPS IMAGE:", image_path.name)
        print("TIPS CLOUDINARY URL:", tips_url)


    run_trend_hunter()
    run_seo_generator()
    run_video_creator()
    run_runway_reel_creator()
    video_files = sorted(
    (PROJECT_DIR / "generated" / "video_scripts").glob("*.json"),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
    )

    latest_video = {}

    if video_files:
        with video_files[0].open("r", encoding="utf-8") as f:
            latest_video = json.load(f)

    ai_title = latest_video.get("title", "")
    ai_caption = latest_video.get("caption", "")

    runway_reels = sorted(
        (PROJECT_DIR / "generated" / "runway_reels").glob("*_FINAL.mp4"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if runway_reels:
        print(f"PUBLISHING RUNWAY REEL: {runway_reels[0].name}")
        publish_reel(runway_reels[0], ai_caption or ai_title)
    headline_variants = [
        ai_title,
        f"AI FOOTBALL ALERT: {ai_title}",
        f"WHAT YOU NEED TO KNOW: {ai_title}",
    ]

    scores_file = GENERATED_DIR / "ab_variant_scores.json"

    winner = None

    if scores_file.exists():
        try:
            with scores_file.open("r", encoding="utf-8") as f:
                score_data = json.load(f)
                winner = score_data.get("winner")
        except Exception as e:
            print(f"A/B winner read failed: {e}")

    winner_index = {
        "A": 0,
        "B": 1,
        "C": 2,
    }.get(winner)

    if winner_index is not None and random.random() < 0.70:
        ab_variant = headline_variants[winner_index]
    else:
        ab_variant = random.choice(headline_variants)
    ai_title = ab_variant
    ab_log_file = GENERATED_DIR / "ab_headline_log.jsonl"

    variant_name = (
        "A" if ai_title == headline_variants[0]
        else "B" if ai_title == headline_variants[1]
        else "C"
    )


    print(f"A/B headline selected: {ai_title}")

    print(f"AI title: {ai_title}")
    print(f"AI caption: {ai_caption}")

    ai_image_path = None

    if ai_title and ai_caption:
        ai_image_path = Path(create_ai_news_image(ai_title, ai_caption))
        print(f"AI news image created: {ai_image_path}")

    x_post_id = post_to_x(ai_image_path, ai_caption)
    print(f"Captured X Post ID: {x_post_id}")
    with ab_log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "variant": variant_name,
            "headline": ai_title,
            "x_post_id": x_post_id,
        }) + "\n")

    upload_result = cloudinary.uploader.upload(
        str(ai_image_path),
        folder="magbets_ai",
        resource_type="image",
    )

    image_url = upload_result.get("secure_url")
    if not image_url:
        raise RuntimeError("Cloudinary did not return a secure image URL.")

    with ai_image_path.open("rb") as image_file:
        response = requests.post(
            MAKE_WEBHOOK_URL,
            files={
                "image": (
                    ai_image_path.name,
                    image_file,
                    "image/jpeg",
                )
            },
            data={
                "filename": ai_image_path.name,
                "caption": ai_caption,
                "image_url": image_url,
                "ab_variant": variant_name,
                "ab_headline": ai_title,
            },
            timeout=90,
        )

    response.raise_for_status()

    print(f"Cloudinary URL: {image_url}")
    print(f"Generated and sent successfully: {ai_image_path.name}")


if __name__ == "__main__":
    main()
