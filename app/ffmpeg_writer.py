import subprocess
from pathlib import Path
from config.config import CONFIG


def cut_segment(input_video, output_video, start, end):
    cmd = [
        CONFIG.FFMPEG_PATH,
        "-y",
        "-ss", f"{start}",
        "-to", f"{end}",
        "-i", input_video,
        "-c:v", "copy",
        "-c:a", "copy",
        output_video,
    ]
    subprocess.run(cmd, check=True)


def save_segments(input_path : Path, segments : list[tuple], output_path : Path):
    for i, (start, end) in enumerate(segments):
        segment_path = output_path / f"{i:04d} {start:.3f}-{end:.3f}{input_path.suffix}"
        cut_segment(input_path, segment_path, start, end)
