from datetime import datetime
from pathlib import Path

from services.api_football import get_today_fixtures
from services.predictions import build_daily_tips
from services.graphics import create_tips_image


def build_caption(tips):
    lines = [
        "🔥 MAGBETS AI DAILY TIPS 🔥",
        "",
    ]

    for number, tip in enumerate(tips, start=1):
        lines.append(f"{number}. {tip['match']}")
        lines.append(
            f"✅ {tip['prediction']} — {tip['confidence']}%"
        )
        lines.append("")

    lines.extend([
        "Predictions are not guaranteed.",
        "18+ | Bet responsibly.",
        "",
        "#Magbets #MagbetsAI #FootballTips #BetResponsibly",
    ])

    return "\n".join(lines)


def run_daily_job():
    fixtures = get_today_fixtures()
    tips = build_daily_tips(fixtures, limit=5)

    if not tips:
        raise RuntimeError("No suitable fixtures were found today.")

    image_path = create_tips_image(tips)
    caption = build_caption(tips)

    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)

    caption_path = output_dir / (
        datetime.now().strftime("caption_%Y%m%d_%H%M%S.txt")
    )
    caption_path.write_text(caption, encoding="utf-8")

    return {
        "image": image_path,
        "caption": str(caption_path),
        "tips": tips,
    }


if __name__ == "__main__":
    result = run_daily_job()

    print("Daily Magbets content created")
    print("Image:", result["image"])
    print("Caption:", result["caption"])
