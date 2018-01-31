import logging.handlers
import os.path

logger = logging.getLogger('eos')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

log_dir = os.path.join(os.path.dirname(__file__), 'log')
if not os.path.exists(log_dir):
    os.mkdir(log_dir, 0o755)
filename = os.path.join(log_dir, 'app.log')
file_handler = logging.handlers.RotatingFileHandler(filename,
                                                    mode='a',
                                                    maxBytes=50 * 1024 * 1024,
                                                    backupCount=5,
                                                    encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
