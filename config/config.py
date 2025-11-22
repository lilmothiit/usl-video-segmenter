import logging
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode


class ProjectConfig:
    # ==================================================  APP OPTIONS  =================================================
    # ----------------------------------------------------  Logging  ---------------------------------------------------
    LOG_LEVEL = logging.INFO
    LOG_EXCEPTIONS_FROM_ALL = True
    LOG_FORMAT = '%(asctime)s | %(levelname)10s | %(filename)30s:%(lineno)4s | %(funcName)30s() | %(message)s'
    LOG_FILE_SIZE = 2*1024*1024
    LOG_FILE_COUNT = 10

    # ---------------------------------------------------  Downloads  --------------------------------------------------
    # REQUESTS_PER_SECOND = 5
    # DOWNLOAD_SPEED = 5_000_000  # bits/sec

    # -----------------------------------------------------  Files  ----------------------------------------------------
    DOWNLOAD_PATH = 'D:/projects/usl-videos/Суспільне Студія'
    SEGMENTS_PATH = 'D:/projects/video-segmenter/data'

    # ----------------------------------------------------  System  ----------------------------------------------------
    SYSTEM_SHUTDOWN_ON_END = False

    # ===============================================  VIDEO PROCESSING  ===============================================
    VIDEO_PROCESSING_LIMIT = 1

    # ------------------------------------------------  Pose Estimation  -----------------------------------------------
    POSE_ESTIMATE_FPS = 12
    POSE_ESTIMATION_OPTIONS = {
        'base_options': BaseOptions(
            model_asset_path='model/pose_landmarker_heavy.task'),
        'running_mode': VisionTaskRunningMode.VIDEO,
        'num_poses': 1,
        'min_pose_detection_confidence': 0.5,
        'min_pose_presence_confidence': 0.5,
        'min_tracking_confidence': 0.5,
        'output_segmentation_masks': False,
    }

    POSE_LANDMARK_CHECKLIST = [15, 16, 17, 18, 19, 20, 21, 22]
    POSE_LANDMARK_VISIBILITY_CRITERIA = 0.8
    POSE_LANDMARK_PRESENCE_CRITERIA = 0.8

    # ------------------------------------------------  Video Handling  ------------------------------------------------
    # PRE_PADDING_SECONDS = 5
    # POST_PADDING_SECONDS = 5

    ROI_WIDTH = 0.25
    ROI_HEIGHT = 0.45
    ROI_CORNER = 'bottom_right'     # one of ["top_left", "top_right", "bottom_left", "bottom_right"]

    VIDEO_EXTENSION = '.mkv'        # mkv supports almost any codec, mp4 needs mp4v, webm needs vp80/vp90
    VIDEO_CODEC = 'mp4v'


CONFIG = ProjectConfig()
