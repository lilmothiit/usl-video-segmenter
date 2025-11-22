from config.config import CONFIG
from util.global_logger import GLOBAL_LOGGER as LOG
from util.path_resolver import PATH_RESOLVER as REPATH
from util.shutdown import shutdown
from app.segmenter import segment_video


def main():
    download_contents = REPATH.DOWNLOAD_DIR.iterdir()
    if not any(download_contents):
        LOG.error("No content found in data directory.")

    limiter_counter = 0

    for item in download_contents:
        if item.is_dir():
            continue

        if not item.suffix.lower() in [".mp4", '.mkv', '.webm']:
            continue

        video_name = item.name
        video_id = video_name.split(" - ")[0]
        video_path = REPATH.SEGMENTS_DIR / video_id
        video_path.mkdir(parents=True, exist_ok=True)

        segment_video(item, video_path)
        limiter_counter += 1

        if limiter_counter >= CONFIG.VIDEO_PROCESSING_LIMIT:
            break

    if CONFIG.SYSTEM_SHUTDOWN_ON_END:
        shutdown()


if __name__ == "__main__":
    main()
