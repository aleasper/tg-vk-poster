import logging


def get_logger():
    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log.log', mode='w')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    return logger
