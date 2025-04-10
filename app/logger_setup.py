from loguru import logger
import os
import sys
from settings import LOGS_PATH, LOG_FILE
from os.path import isfile, join, exists

def setup_logger():
    if not exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)

    log_path = os.path.join(LOGS_PATH, LOG_FILE)

    logger.remove()  

    # В терминал (удобно при разработке)
    logger.add(sys.stdout, 
               format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}", 
               colorize=True)

    # В файл
    logger.add(log_path,
               format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}",
               level="DEBUG",
               rotation="10 MB",
               retention="10 days",
               compression="zip",
               backtrace=True,
               diagnose=True)
