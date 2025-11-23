import cv2
import mediapipe as mp

from pathlib import Path
from mediapipe.tasks.python.vision import PoseLandmarkerOptions, PoseLandmarker

from config.config import CONFIG
from util.global_logger import GLOBAL_LOGGER as LOG


_TASK_OPTIONS = PoseLandmarkerOptions(**CONFIG.POSE_ESTIMATION_OPTIONS)

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


def estimate_pose(estimator, image, image_msec):
    image = extract_roi(image, CONFIG.ROI_WIDTH, CONFIG.ROI_HEIGHT, CONFIG.ROI_CORNER)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
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


def segment_video(input_video : Path) -> list[tuple]:
    """
    Process input video file with PoseLandmarker and save video segments.
    :param input_video: path to input video file
    :return: list of tuples with (start, end) seconds
    """

    # estimator is created per video
    _POSE_ESTIMATOR = PoseLandmarker.create_from_options(_TASK_OPTIONS)

    LOG.info(f'Processing video {input_video}')
    in_vid = cv2.VideoCapture(str(input_video))

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

    segments = []
    segment_start = None

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

        pose_detected = estimate_pose(_POSE_ESTIMATOR, image, int(in_vid.get(cv2.CAP_PROP_POS_MSEC)))

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

    in_vid.release()
    return segments
