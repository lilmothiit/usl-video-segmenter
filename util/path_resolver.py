from pathlib import Path
from config.config import CONFIG


class PathResolver:
    # project paths
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    LOG_DIR = PROJECT_ROOT / 'logs'

    DOWNLOAD_DIR = Path(CONFIG.DOWNLOAD_PATH)
    SEGMENTS_DIR = Path(CONFIG.SEGMENTS_PATH)

    def __init__(self):
        for attr in dir(self):
            if attr.endswith('_DIR'):
                getattr(self, attr).mkdir(parents=True, exist_ok=True)

    def exists(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
        return path.exists()


PATH_RESOLVER = PathResolver()

