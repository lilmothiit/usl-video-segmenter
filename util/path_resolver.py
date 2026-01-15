from pathlib import Path
from config.app_config import CONFIG


class PathResolver:
    # project paths
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    LOG_PATH = PROJECT_ROOT / 'logs'

    def __init__(self):
        for attr in dir(CONFIG):
            # copy all paths from config
            if attr.endswith('_PATH'):
                setattr(self, attr, Path(getattr(CONFIG, attr)))
                
                # if path is a directory, make sure it exists
                if getattr(self, attr).is_dir():
                    getattr(self, attr).mkdir(parents=True, exist_ok=True)

    def exists(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = self.PROJECT_ROOT / path
        return path.exists()


PATH_RESOLVER = PathResolver()

