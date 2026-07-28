from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1350
OUTPUT_DIR = Path("generated")


def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def fit_font(draw, text, maximum_width, starting_size=42, bold=False):
    size = starting_size

    while size >= 20:
        font = get_font(size, bold)
        box = draw.textbbox((0, 0), text, font=font)

        if box[2] - box[0] <= maximum_width:
            return font

        size -= 2

    return get_font(20, bold)


def create_tips_image(tips):
    OUTPUT_DIR.mkdir(exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), (8, 14, 11))
    draw = ImageDraw.Draw(image)

    green = (10, 215, 132)
    dark_green = (5, 102, 63)
    card_colour = (22, 30, 26)
    grey = (175, 185, 179)
    white = (255, 255, 255)

    draw.rounded_rectangle(
        (45, 45, WIDTH - 45, 195),
        radius=30,
        fill=dark_green,
    )

    draw.text(
        (75, 65),
        "MAGBETS",
        font=get_font(62, True),
        fill=green,
    )

    draw.text(
        (75, 138),
        "AI DAILY FOOTBALL TIPS",
        font=get_font(29, True),
        fill=white,
    )

    draw.text(
        (WIDTH - 75, 105),
        datetime.now().strftime("%d %b %Y"),
        font=get_font(25),
        fill=white,
        anchor="ra",
    )

    y = 235
    card_height = 175

    for number, tip in enumerate(tips[:5], start=1):
        draw.rounded_rectangle(
            (45, y, WIDTH - 45, y + card_height),
            radius=25,
            fill=card_colour,
        )

        draw.ellipse(
            (68, y + 52, 128, y + 112),
            fill=dark_green,
        )

        draw.text(
            (98, y + 82),
            str(number),
            font=get_font(28, True),
            fill=white,
            anchor="mm",
        )

        match_text = tip.get("match", "Football Match")
        league_text = tip.get("league", "Football")
        kickoff = tip.get("kickoff", "")
        prediction = tip.get("prediction", "Prediction unavailable")
        confidence = tip.get("confidence", 0)

        draw.text(
            (155, y + 22),
            match_text,
            font=fit_font(draw, match_text, 760, 36, True),
            fill=white,
        )

        details = f"{league_text}  |  {kickoff}"

        draw.text(
            (155, y + 70),
            details,
            font=fit_font(draw, details, 750, 23),
            fill=grey,
        )

        draw.text(
            (155, y + 110),
            prediction,
            font=fit_font(draw, prediction, 610, 31, True),
            fill=green,
        )

        draw.rounded_rectangle(
            (835, y + 103, 990, y + 150),
            radius=18,
            fill=dark_green,
        )

        draw.text(
            (912, y + 126),
            f"{confidence}%",
            font=get_font(27, True),
            fill=white,
            anchor="mm",
        )

        y += card_height + 18

    draw.line(
        (65, 1225, WIDTH - 65, 1225),
        fill=(70, 82, 75),
        width=2,
    )

    draw.text(
        (65, 1260),
        "@magbets.ng",
        font=get_font(29, True),
        fill=green,
    )

    draw.text(
        (WIDTH - 65, 1260),
        "18+ | Bet responsibly",
        font=get_font(24),
        fill=grey,
        anchor="ra",
    )

    filename = datetime.now().strftime("magbet_tips_%Y%m%d_%H%M%S.jpg")
    output_path = OUTPUT_DIR / filename
    image.save(output_path, quality=94)

    return str(output_path)
