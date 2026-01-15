from config.config import CONFIG
from util.global_logger import GLOBAL_LOGGER as LOG
from util.path_resolver import PATH_RESOLVER as REPATH
from util.shutdown import shutdown

from app.segmenter import segment_video, load_segments, save_segments
from app.ffmpeg_writer import mux_cut_segments
from app.postprocessing import merge_and_filter


def main():
    download_contents = REPATH.DOWNLOAD_PATH.iterdir()
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
        video_out_path = REPATH.SEGMENTS_PATH / CONFIG.SEGMENTATION_MODE / video_id
        video_out_path.mkdir(parents=True, exist_ok=True)

        if CONFIG.PERFORM_SEGMENTATION:
            segments = segment_video(item, video_out_path)
        else:
            segments = load_segments(video_out_path, '.meta.post')
            # try to load .meta segments and postprocess them
            if not segments:
                segments = load_segments(video_out_path)
                segments = merge_and_filter(segments, video_out_path)
                save_segments(video_out_path, segments, '.meta.post')

        if not segments:
            continue

        if CONFIG.CUT_VIDEO_SEGMENTS:
            mux_cut_segments(item, segments, video_out_path)

        limiter_counter += 1
        if limiter_counter >= CONFIG.VIDEO_PROCESSING_LIMIT:
            break

    if CONFIG.SYSTEM_SHUTDOWN_ON_END:
        shutdown()


if __name__ == "__main__":
    main()
