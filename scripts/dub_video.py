"""CLI: dub a Spanish MP4 with a single ElevenLabs voice.

    python scripts/dub_video.py input.mp4 -o out_dir [--subtitles] [--burn] [--whisper small]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services import dubbing  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("-o", "--output-dir", default="storage/dubbing")
    p.add_argument("--whisper", default="small", help="tiny/base/small/medium/large-v3")
    p.add_argument("--model", default=dubbing.DEFAULT_TTS_MODEL)
    p.add_argument("--subtitles", action="store_true", help="write SRT")
    p.add_argument("--burn", action="store_true", help="burn subtitles into the video")
    a = p.parse_args()
    r = dubbing.dub_video(
        a.video, a.output_dir, model_id=a.model, whisper_model=a.whisper,
        subtitles=a.subtitles or a.burn, burn_subtitles=a.burn,
        progress=lambda s, f, m: print(f"[{s}] {f:.0%} {m}", flush=True),
    )
    print("OUTPUT:", r.output_video)
    print("SRT:", r.srt_path)
    for w in r.warnings:
        print("WARN:", w)


if __name__ == "__main__":
    main()
