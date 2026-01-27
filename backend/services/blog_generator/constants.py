"""
blog_generator 常量定义
"""

import os


def _get_int_env(name: str, default: int) -> int:
    """安全读取整型环境变量，异常时回退默认值。"""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# Reviewer 通过阈值（可通过环境变量 REVIEW_THRESHOLD 覆盖）
REVIEW_THRESHOLD = _get_int_env("REVIEW_THRESHOLD", 91)

