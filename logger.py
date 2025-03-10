import logging
from colorama import Fore, Style, init

# create custom log

init()

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.DEBUG:
            color = Fore.CYAN
        elif record.levelno == logging.INFO:
            color = Fore.GREEN
        elif record.levelno == logging.WARNING:
            color = Fore.YELLOW
        elif record.levelno == logging.ERROR:
            color = Fore.RED
        elif record.levelno == logging.CRITICAL:
            color = Fore.RED + Style.BRIGHT
        else:
            color = Style.RESET_ALL
        record.levelname = color + record.levelname + Style.RESET_ALL
        record.msg = color + str(record.msg) + Style.RESET_ALL
        return super().format(record)
    
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(levelname)s: %(message)s"))

log.addHandler(handler)