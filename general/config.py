import os.path

import tomli as tomllib

PYPROJECT = "pyproject.toml"
PYPROJECT_DEFAULT = "pyproject.default.toml"


class Config:
    config = None
    if not os.path.exists(PYPROJECT) and os.path.exists(PYPROJECT_DEFAULT):
        import shutil
        print(f"copying {PYPROJECT_DEFAULT} to {PYPROJECT} for first run")
        shutil.copyfile(PYPROJECT_DEFAULT, PYPROJECT)

    try:
        with open(PYPROJECT, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{PYPROJECT} not found")

    @classmethod
    def get(cls, *path):
        result = cls.config
        for item in path:
            result = result.get(item, None)
            if result is None:
                break
        return result
