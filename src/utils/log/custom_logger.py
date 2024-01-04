from loguru import logger
import sys
import os

def set_logger():
    is_debug = int(os.environ.get("is_debug",0))
    if is_debug:
        level="DEBUG"
    else:
        level = "INFO"

    logger.remove()
    logger.add(sys.stdout, colorize=True, format="{time:YYYY-MM-DD HH:mm:ss.ms} | {level} | {module}|{function}|{line} | {message} | uuid: {extra[uuid]}", level=level)