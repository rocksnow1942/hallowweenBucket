import logging 
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections import deque

def systemLogFile(logfileName):
    folder = Path(__file__).parent
    fh = RotatingFileHandler( folder / logfileName, maxBytes=2**23, backupCount=10)
    # fh.setLevel(level)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s|%(name)-11s|%(levelname)-8s: %(message)s', datefmt='%m/%d %H:%M:%S'
    ))
    return fh

class Logger():
    def debug(self, x): return 0
    def info(self, x): return 0
    def warning(self, x): return 0
    def error(self, x): return 0
    def critical(self, x): return 0

    def __init__(self,saveName, logLevel='DEBUG', printMessages = True,fileHandler=None, **kwargs):
        self.PRINT_MESSAGES = printMessages
        self.LOG_LEVEL = logLevel

        # to store messages.
        self.msgDeque = deque(maxlen=100)
        
        self.init_logger(saveName,fileHandler)
    
    def init_logger(self,logfileName,fileHandler):
        PRINT_MESSAGES = self.PRINT_MESSAGES
        LOG_LEVEL = self.LOG_LEVEL
        level = getattr(logging, LOG_LEVEL.upper(), 20)
        logger = logging.getLogger(logfileName)
        logger.handlers = []
        logger.addHandler(fileHandler)
        logger.setLevel(level)
        
        self.logger = logger

        def wrapper(func):
            def wrap(msg,error=None):
                "possibly send msg to a stream for display elsewhere."
                print(msg)
                self.msgDeque.appendleft(msg)
                return func(msg)
            return wrap

        _log_level = ['debug', 'info', 'warning', 'error', 'critical']
        _log_index = _log_level.index(LOG_LEVEL.lower())

        for i in _log_level:
            setattr(self, i, getattr(self.logger, i))

        
        if PRINT_MESSAGES:  # if print message, only print for info above that level.
            for i in _log_level[_log_index:]:
                setattr(self, i, wrapper(getattr(self.logger, i)))