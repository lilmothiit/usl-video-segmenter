# USL Video Segmenter

A project for automatic segmentation and cutting/muxing of USL videos.

## Current features

- Segmentation based on Pose Estimation (slower) or Hand Estimation (faster)
- ROI configuration
- Persistence, segment and video processing limits
- Video cutting padding, min length

## Installation
1. Clone the repo
    
    ```bash
    git clone https://github.com/lilmothiit/usl-video-segmenter
    ```

2. Install requirements
    
    ```bash
   pip install -r requirements.txt
   ```

3. Download support tools:
   - [yt-dlp](https://github.com/yt-dlp/yt-dlp)
   - [ffmpeg](https://ffmpeg.org/).

4. Place the files in a desired location. Default location is:
    ```
   <Project Root>/tools/
   ```
5. Download [Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) and/or [Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) tasks.
6. Place in a desired location. Default location is:
    ```
   <Project Root>/model/
   ```

7. Configure project in `app_config.py`
8. Configure download options in `ytdlp_config.txt`

## Usage

1. Download videos using the provided `download.bat`
2. Launch `main.py` to start segmentation. Cutting/muxing happens at the end of segmentation for optimization.