from pathlib import Path

from config.config import CONFIG
from app.segmenter import save_segments


def merge_and_filter(segments, video_out_path: Path):
    # Sort segments by start time
    segments = sorted(segments, key=lambda x: x[0])
    merged = []

    for start, end in segments:
        if not merged:
            merged.append([start, end])
            continue

        last_start, last_end = merged[-1]

        # Merge overlap or touching (end == start) segments
        if start <= last_end:
            merged[-1][1] = max(last_end, end)
        else:
            merged.append([start, end])

    # Remove short segments
    cleaned = [
        (s, e) for s, e in merged
        if (e - s) >= CONFIG.SEGMENT_MIN_LENGTH
    ]

    save_segments(video_out_path, cleaned, '.meta.post')

    return cleaned

