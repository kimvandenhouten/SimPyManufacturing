import tomli as tomllib


class Config:
    config = None
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("pyproject.toml not found")

    @classmethod
    def get(cls, *path):
        result = cls.config
        for item in path:
            result = result.get(item, None)
            if result is None:
                break
        return result
