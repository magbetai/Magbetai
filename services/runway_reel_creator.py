from dotenv import load_dotenv
load_dotenv("/root/Magbetai/.env")
from pathlib import Path
from services.approved_reel_audio import add_approved_audio
import json
import os
import re
import time
import random
import subprocess
import requests


PROJECT_DIR = Path("/root/Magbetai")
ENV_FILE = PROJECT_DIR / ".env"
SCRIPT_DIR = PROJECT_DIR / "generated" / "video_scripts"
OUTPUT_DIR = PROJECT_DIR / "generated" / "runway_reels"
WORK_DIR = OUTPUT_DIR / "work"

API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_VERSION = "2024-11-06"

MODEL = "gen4.5"
RATIO = "720:1280"
SCENE_DURATION = 5
MAX_SCENES = 4


def load_env():
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def clean(value):
    return str(value or "").strip()


def slugify(text):
    text = clean(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:90] or "magbets-runway-reel"


def latest_script():
    files = sorted(
        SCRIPT_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not files:
        raise FileNotFoundError(
            f"No video scripts found in {SCRIPT_DIR}"
        )

    path = files[0]

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Using script: {path.name}")

    return data


def build_scene_prompts(data):

    title = clean(data.get("title"))
    voiceover = clean(data.get("voiceover")) or title

    lower_title = title.lower()

    # Build proper visual storytelling instead of generic filler.

    if "transfer" in lower_title or "signing" in lower_title:

        scene_ideas = [

            f"A professional African football striker connected with this story: {title}. He arrives outside a major Spanish football stadium at dusk, stepping from a premium team vehicle, realistic press cameras nearby, transfer-day atmosphere.",

            f"The same professional football striker during a realistic medical and fitness assessment inside a modern elite football training facility, sports scientists and club staff working around him, premium documentary camera style.",

            f"The football striker walks through a dramatic stadium tunnel toward the pitch wearing a clean red-and-white inspired professional football kit with no logos, floodlights ahead, realistic transfer unveiling atmosphere.",

            f"The striker stands pitch-side inside a packed Spanish-style football stadium while supporters celebrate in the background, cinematic press-day reveal, camera slowly circles him, premium European football commercial look.",

        ]

    elif "injury" in lower_title:

        scene_ideas = [

            f"Professional football training session related to this story: {title}. A player suddenly pulls up during an intense drill, realistic teammates reacting, documentary sports camera.",

            "Professional football medical staff carefully assessing an injured player's leg inside a modern training facility, realistic sports medicine environment.",

            "The player walking through a stadium tunnel during recovery, determined expression, cinematic slow tracking shot, premium sports documentary.",

            "Professional footballer returning to light training on a pristine pitch under stadium floodlights, hopeful comeback atmosphere.",

        ]

    elif "champions league" in lower_title or "match" in lower_title:

        scene_ideas = [

            f"Massive European football stadium before an important match connected to this story: {title}, supporters arriving, dramatic evening floodlights, cinematic aerial-to-ground camera.",

            "Professional football players warming up intensely on the pitch, realistic movement and broadcast-quality sports cinematography.",

            "High-intensity football action near the penalty area, realistic professional players, fast tracking camera, dramatic crowd atmosphere.",

            "Players leaving the pitch after the match while supporters react in the stands, cinematic football documentary ending.",

        ]

    else:

        scene_ideas = [

            f"Premium cinematic football opening inspired by this story: {title}. Professional football stadium at night, realistic players entering the pitch, dramatic floodlights and crowd atmosphere.",

            f"Professional football training and preparation connected to this football story: {title}, realistic athletes and coaching staff, premium sports documentary.",

            f"Football press and stadium atmosphere related to this story: {title}, realistic professional player walking through media area toward the pitch.",

            f"Packed football stadium finale related to this story: {title}, supporters celebrating under bright floodlights, cinematic professional sports commercial.",

        ]

    scene_ideas = scene_ideas[:MAX_SCENES]

    prompts = []

    for i, idea in enumerate(scene_ideas, start=1):

        prompt = (

            "Cinematic photorealistic professional association football video. "

            f"Scene {i}: {idea} "

            "Real-world sports documentary realism. Natural human movement and anatomy, "

            "realistic skin, realistic fabric and lighting, believable professional football environment. "

            "Premium European and African football broadcast cinematography, dynamic but controlled camera movement, "

            "cinematic depth of field, atmospheric stadium lighting, polished advertising production. "

            "People must look physically realistic and consistent. "

            "No written text, no captions, no subtitles, no logos, no trademarks, no watermark, "

            "no distorted faces, no duplicate people, no extra fingers, no extra limbs, no surreal objects."

        )

        # Runway text-to-video allows max 1000 prompt characters.
        prompt = prompt[:950]
        prompts.append(prompt)

    return title, prompts

def headers():
    key = os.getenv("RUNWAY_API_KEY")

    if not key:
        raise RuntimeError(
            "RUNWAY_API_KEY is missing from /root/Magbetai/.env"
        )

    return {
        "Authorization": f"Bearer {key}",
        "X-Runway-Version": RUNWAY_VERSION,
        "Content-Type": "application/json",
    }


def create_task(prompt):
    payload = {
        "model": MODEL,
        "promptText": "Cinematic photorealistic professional football news footage. Professional football players training and arriving at a modern stadium, matchday atmosphere, press cameras, stadium tunnel and football pitch. Natural realistic human movement, premium sports broadcast cinematography. No identifiable public figures, no famous people, no written text, no logos, no trademarks.",
        "ratio": RATIO,
        "duration": SCENE_DURATION,
    }

    response = requests.post(
        f"{API_BASE}/text_to_video",
        headers=headers(),
        json=payload,
        timeout=60,
    )

    if not response.ok:
        print("RUNWAY ERROR:", response.status_code, response.text)
    response.raise_for_status()

    data = response.json()

    task_id = data["id"]

    estimated = (
        data.get("estimatedCost", {})
        .get("credits")
    )

    print(f"Task created: {task_id}")

    if estimated is not None:
        print(f"Estimated credits: {estimated}")

    return task_id


def wait_for_task(task_id):
    attempt = 0

    while True:
        attempt += 1

        response = requests.get(
            f"{API_BASE}/tasks/{task_id}",
            headers=headers(),
            timeout=60,
        )

        if not response.ok:
            print("RUNWAY ERROR:", response.status_code, response.text)
        response.raise_for_status()

        data = response.json()

        status = data.get("status", "UNKNOWN")

        print(
            f"Task {task_id[:8]} status: {status}"
        )

        if status == "SUCCEEDED":
            output = data.get("output") or []

            if not output:
                raise RuntimeError(
                    "Runway task succeeded but returned no output."
                )

            return output[0]

        if status in ("FAILED", "CANCELED"):
            raise RuntimeError(
                f"Runway task ended with status: {status} | DETAILS: {data}"
            )

        delay = 6 + random.uniform(0, 2)

        time.sleep(delay)


def download_video(url, destination):
    print(
        f"Downloading {destination.name}..."
    )

    response = requests.get(
        url,
        timeout=180,
    )

    if not response.ok:
        print("RUNWAY ERROR:", response.status_code, response.text)
    response.raise_for_status()

    destination.write_bytes(
        response.content
    )

    print(
        f"Saved: {destination} "
        f"({destination.stat().st_size} bytes)"
    )


def validate_clip(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=width,height,duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    print(
        f"Validated: {path.name}"
    )

    return json.loads(
        result.stdout
    )


def join_clips(clips, output):
    concat_file = (
        WORK_DIR / "concat.txt"
    )

    lines = [
        f"file '{clip}'"
        for clip in clips
    ]

    concat_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("Joining Runway scenes...")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def main():
    load_env()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    WORK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = latest_script()

    title, prompts = (
        build_scene_prompts(data)
    )

    print()
    print("==============================")
    print("MAGBETS RUNWAY REEL CREATOR")
    print("==============================")
    print(f"Title: {title}")
    print(f"Scenes: {len(prompts)}")
    print(
        f"Planned duration: "
        f"{len(prompts) * SCENE_DURATION}s"
    )
    print()

    clips = []

    for index, prompt in enumerate(
        prompts,
        start=1,
    ):
        print(
            f"--- Scene {index}/{len(prompts)} ---"
        )

        print(
            f"Prompt: {prompt}"
        )

        task_id = create_task(
            prompt
        )

        video_url = wait_for_task(
            task_id
        )

        clip_path = (
            WORK_DIR
            / f"runway_scene_{index:02d}.mp4"
        )

        download_video(
            video_url,
            clip_path,
        )

        validate_clip(
            clip_path
        )

        clips.append(
            clip_path
        )

        print()

    final_path = (
        OUTPUT_DIR
        / (
            slugify(title)
            + "_runway_reel.mp4"
        )
    )

    join_clips(
        clips,
        final_path,
    )

    final_path = add_approved_audio(final_path, data)

    print()
    print("==============================")
    print("RUNWAY REEL CREATED")
    print("==============================")
    print(f"Scenes: {len(clips)}")
    print(
        f"Duration target: "
        f"{len(clips) * SCENE_DURATION}s"
    )
    print(f"Video: {final_path}")


if __name__ == "__main__":
    main()
