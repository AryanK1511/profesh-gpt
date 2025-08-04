import logging
import logging.config
import time

from colorama import Fore, Style
from colorama import init as colorama_init

from src.common.config import settings

colorama_init(autoreset=True)

COLORS = {
    "DEBUG": Fore.LIGHTBLACK_EX,
    "INFO": Fore.LIGHTBLUE_EX,
    "WARNING": Fore.LIGHTYELLOW_EX,
    "ERROR": Fore.LIGHTRED_EX,
    "CRITICAL": Fore.LIGHTMAGENTA_EX,
}
RESET = Style.RESET_ALL


class UvicornLikeFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record):
        level_color = COLORS.get(record.levelname, "")
        colored_level = f"{level_color}{record.levelname}{RESET}"

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", self.converter(record.created))
        colored_timestamp = f"{Fore.LIGHTGREEN_EX}{timestamp}{RESET}"

        module_path = f"{record.module}:{record.funcName}:{record.lineno}"
        colored_module_path = f"{Fore.LIGHTCYAN_EX}{module_path}{RESET}"

        formatted_message = f"{colored_timestamp} | {colored_level} | {colored_module_path} - {record.getMessage()}"

        return formatted_message


def setup_logging():
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = {
        "format": "%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d - %(message)s",
        "datefmt": date_fmt,
        "()": UvicornLikeFormatter,
    }
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": formatter,
        },
        "handlers": {
            "default": {
                "level": settings.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(logging_config)


def get_logger():
    return logging.getLogger()


logger = get_logger()
