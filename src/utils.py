from typing import Optional


def is_empty(text: str) -> bool:
    return not text or str(text).isspace()

def update_if_not_empty(target: dict, key: str, value: str) -> dict:
    if not is_empty(value):
        target[key] = value
    return target

def update_key_if_not_empty(source: dict, target: dict, key: str) -> dict:
    return update_if_not_empty(target, key, source.get(key, None))

def get_value(data: dict, default: Optional[str]=None, *path: str) -> Optional[str]:
    result = data
    for arg in path:
        if arg in result:
            result = result[arg]
        else:
            return default
    return result
