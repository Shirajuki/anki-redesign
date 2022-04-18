import os
import logging
# declare an empty logger class
class EmptyLogger():
    def debug(self, *_):
        return None
logger = EmptyLogger()
# init logger
if 'ANKI_REDESIGN_DEBUG_LOGGING' in os.environ:
    filename =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user_files", "test.log")
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    datefmt='%Y%m%d-%H:%M:%S',
    filename=filename, 
    level=logging.DEBUG)
    logger = logging.getLogger('anki-redesign')
    logger.setLevel(logging.DEBUG)
    logger.debug("Initialized anki")
