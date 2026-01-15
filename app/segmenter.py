from sys import meta_path

import cv2
import json
import mediapipe as mp

from pathlib import Path
from mediapipe.tasks.python.vision import PoseLandmarkerOptions, PoseLandmarker, HandLandmarkerOptions, HandLandmarker

from config.app_config import CONFIG
from util.global_logger import GLOBAL_LOGGER as LOG


_ROI_ANCHORS = {
    "top_left":     (0, 0),
    "top_right":    (1, 0),
    "bottom_left":  (0, 1),
    "bottom_right": (1, 1),
}


def extract_roi(img, w_ratio, h_ratio, corner):
    h, w = img.shape[:2]

    roi_w = int(w * w_ratio)
    roi_h = int(h * h_ratio)

    ax, ay = _ROI_ANCHORS[corner]

    x0 = ax * (w - roi_w)
    y0 = ay * (h - roi_h)

    return img[y0:y0 + roi_h, x0:x0 + roi_w]


def aspect_wise_resize(image, new_size):
    h, w = image.shape[:2]
    new_h, new_w = new_size

    scale = new_w / w
    new_h = int(h * scale)

    return cv2.resize(image, (new_w, new_h))


def preprocess_image(image):
    image = extract_roi(image, CONFIG.ROI_WIDTH, CONFIG.ROI_HEIGHT, CONFIG.ROI_CORNER)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    return mp_image


def estimate_pose(estimator, image, image_msec):
    mp_image = preprocess_image(image)
    result = estimator.detect_for_video(mp_image, image_msec)

    if not result.pose_landmarks:
        return False

    hands_detected = False

    for index in CONFIG.POSE_LANDMARK_CHECKLIST:
        landmark = result.pose_landmarks[0][index]
        if (landmark.visibility >= CONFIG.POSE_LANDMARK_VISIBILITY_CRITERIA
                and landmark.presence >= CONFIG.POSE_LANDMARK_PRESENCE_CRITERIA):
            hands_detected = True

    return hands_detected


def estimate_hand(estimator, image, image_msec):
    mp_image = preprocess_image(image)
    result = estimator.detect_for_video(mp_image, image_msec)

    return True if result.hand_landmarks else False


def estimation_pipe(input_path: Path, output_path: Path,
                    known_segments: list[tuple[float, float]],
                    estimator, estimator_func) \
        -> list[tuple[float, float]]:
    """
    Process input video file with PoseLandmarker and save video segments.
    :param output_path: path to output folder
    :param estimator_func: function that preprocesses an image and returns bool based on estimator output
    :param estimator: a model that can process frames
    :param input_path: path to input video file
    :param known_segments: list of known segments
    :return: list of tuples with (start, end) seconds
    """

    # estimator is created per video
    _ESTIMATOR = estimator

    LOG.info(f'Processing video {input_path}')
    in_vid = cv2.VideoCapture(str(input_path))

    if not in_vid.isOpened():
        LOG.error(f"Unknown error opening video file")
        return []

    frame_count = 0
    total_frames = int(in_vid.get(cv2.CAP_PROP_FRAME_COUNT))

    if not total_frames or total_frames <= 0:
        LOG.error(f"Error opening video file: Frame count is equal to or less than 0")
        return []

    video_fps = in_vid.get(cv2.CAP_PROP_FPS)
    frame_step = int(video_fps / CONFIG.POSE_ESTIMATE_FPS)
    LOG.debug(f'Video FPS: {video_fps}, Estimation FPS: {CONFIG.POSE_ESTIMATE_FPS}, Frame step: {frame_step}')

    segments = known_segments
    segment_start = None

    if segments:
        last_segment_end = int(segments[-1][1] * 1000)
        in_vid.set(cv2.CAP_PROP_POS_MSEC, last_segment_end)

    while in_vid.isOpened():
        success, image = in_vid.read()

        if not success:
            LOG.info("Reached end of video")
            break

        frame_count += 1
        if frame_count % frame_step == 0:
            LOG.debug(f"Processing frame {frame_count}/{total_frames}")
        else:
            continue

        pose_detected = estimator_func(_ESTIMATOR, image, int(in_vid.get(cv2.CAP_PROP_POS_MSEC)))

        if pose_detected:
            if segment_start is None:
                segment_start = frame_count
        else:
            if segment_start is not None:
                start_time = segment_start / video_fps - CONFIG.PRE_PADDING_SECONDS
                end_time = frame_count / video_fps + CONFIG.POST_PADDING_SECONDS

                segments.append((start_time, end_time))
                LOG.info(f'Segment {len(segments):04d}: {start_time:.2f}-{end_time:.2f}, '
                         f'total {end_time-start_time:.2f} seconds')
                segment_start = None

        if len(segments) >= CONFIG.VIDEO_SEGMENT_LIMIT:
            break

        if len(segments) % CONFIG.CHECKPOINT_INTERVAL == 0:
            save_segments(output_path, segments)

    in_vid.release()
    return segments


def save_segments(segments_path: Path, segments: list[tuple[float, float]], suffix='.meta') -> None:
    meta_path = segments_path / suffix
    json_ready = [[s, e] for (s, e) in segments]

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(json_ready, f, indent=2)


def load_segments(segments_path: Path, suffix='.meta') -> list[tuple[float, float]]:
    meta_path = segments_path / suffix

    if not meta_path.exists():
        return []

    with meta_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    return [(float(s), float(e)) for s, e in raw]


def segment_video(input_video: Path, output_path : Path) -> list[tuple[float, float]]:
    segments = load_segments(output_path)

    if CONFIG.SEGMENTATION_MODE == 'pose':
        task_options = PoseLandmarkerOptions(**CONFIG.POSE_ESTIMATION_OPTIONS)
        estimator = PoseLandmarker.create_from_options(task_options)
        estimator_func = estimate_pose
    elif CONFIG.SEGMENTATION_MODE == 'hand':
        task_options = HandLandmarkerOptions(**CONFIG.HAND_ESTIMATION_OPTIONS)
        estimator = HandLandmarker.create_from_options(task_options)
        estimator_func = estimate_hand
    else:
        LOG.error(f"Unknown segmentation mode: {CONFIG.SEGMENTATION_MODE}")
        return []

    new_segments = estimation_pipe(input_video, output_path, segments, estimator, estimator_func)

    if new_segments == segments:
        return []

    save_segments(output_path, segments)
    return segments


