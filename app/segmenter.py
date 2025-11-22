import cv2
import mediapipe as mp

from collections import deque
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


def segment_video(input_video : Path, output_dir : Path) -> None:
    """
    Process input video file with PoseLandmarker and save video segments.\
    :param input_video: path to input video file
    :param output_dir: path to output directory
    """

    # estimator is created per video
    _POSE_ESTIMATOR = PoseLandmarker.create_from_options(_TASK_OPTIONS)

    LOG.info(f'Processing video {input_video}')
    in_vid = cv2.VideoCapture(str(input_video))

    if not in_vid.isOpened():
        LOG.error(f"Unknown error opening video file {input_video}")
        return

    segment_count = 0
    frame_count = 0
    total_frames = int(in_vid.get(cv2.CAP_PROP_FRAME_COUNT))

    if not total_frames or total_frames <= 0:
        LOG.error(f"Error opening video file {input_video}: Frame count is equal to or less than 0")
        return

    video_fps = in_vid.get(cv2.CAP_PROP_FPS)
    frame_step = int(video_fps / CONFIG.POSE_ESTIMATE_FPS)
    LOG.debug(f'Video FPS: {video_fps}, Estimation FPS: {CONFIG.POSE_ESTIMATE_FPS}, Frame step: {frame_step}')

    # pre_pad = int(video_fps * CONFIG.PRE_PADDING_SECONDS)
    # post_pad = int(video_fps * CONFIG.POST_PADDING_SECONDS)
    # pre_buffer = deque(maxlen=pre_pad)
    # post_pad_counter = 0

    writer = None

    while in_vid.isOpened():
        success, image = in_vid.read()

        if not success:
            LOG.info("Reached end of video")
            break

        if writer is not None:
            # Write the current frame into the open segment
            writer.write(image)

        frame_count += 1
        if frame_count % frame_step == 0:
            LOG.debug(f"Processing frame {frame_count}/{total_frames}")
        else:
            continue

        pose_detected = estimate_pose(_POSE_ESTIMATOR, image, int(in_vid.get(cv2.CAP_PROP_POS_MSEC)))

        if pose_detected:
            # Start a new segment if none is currently open
            if writer is None:
                segment_out = output_dir / f"{segment_count:04d}{CONFIG.VIDEO_EXTENSION}"

                fourcc = cv2.VideoWriter.fourcc(*CONFIG.VIDEO_CODEC)
                width = int(in_vid.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(in_vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

                writer = cv2.VideoWriter(str(segment_out), fourcc, video_fps, (width, height))
                LOG.info(f"Starting new segment #{segment_count:04d} at {segment_out}")

                writer.write(image)

        else:
            # End the segment if one is open
            if writer is not None:
                writer.release()
                writer = None
                LOG.info(f"Closed segment #{segment_count:04d}")
                segment_count += 1

    in_vid.release()
    return
