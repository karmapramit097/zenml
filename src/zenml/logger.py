#  Copyright (c) ZenML GmbH 2020. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

import logging
import os
import re
import sys
from contextlib import contextmanager
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Iterator

from absl import logging as absl_logging
from rich.traceback import install as rich_tb_install

from zenml.constants import (
    ABSL_LOGGING_VERBOSITY,
    APP_NAME,
    ENABLE_RICH_TRACEBACK,
    ENV_ZENML_SUPPRESS_LOGS,
    ZENML_LOGGING_VERBOSITY,
    handle_bool_env_var,
)
from zenml.enums import LoggingLevels


class CustomFormatter(logging.Formatter):
    """Formats logs according to custom specifications."""

    grey: str = "\x1b[38;21m"
    pink: str = "\x1b[35m"
    green: str = "\x1b[32m"
    yellow: str = "\x1b[33m"
    red: str = "\x1b[31m"
    bold_red: str = "\x1b[31;1m"
    purple: str = "\x1b[1;35m"
    reset: str = "\x1b[0m"

    format_template: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%("
        "filename)s:%(lineno)d)"
        if LoggingLevels[ZENML_LOGGING_VERBOSITY] == LoggingLevels.DEBUG
        else "%(message)s"
    )

    COLORS: Dict[LoggingLevels, str] = {
        LoggingLevels.DEBUG: grey,
        LoggingLevels.INFO: purple,
        LoggingLevels.WARN: yellow,
        LoggingLevels.ERROR: red,
        LoggingLevels.CRITICAL: bold_red,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Converts a log record to a (colored) string

        Args:
            record: LogRecord generated by the code.

        Returns:
            A string formatted according to specifications.
        """
        log_fmt = (
            self.COLORS[LoggingLevels(record.levelno)]
            + self.format_template
            + self.reset
        )
        formatter = logging.Formatter(log_fmt)
        formatted_message = formatter.format(record)
        quoted_groups = re.findall("`([^`]*)`", formatted_message)
        for quoted in quoted_groups:
            formatted_message = formatted_message.replace(
                "`" + quoted + "`",
                self.reset
                + self.yellow
                + quoted
                + self.COLORS.get(LoggingLevels(record.levelno)),
            )
        return formatted_message


LOG_FILE = f"{APP_NAME}_logs.log"


def get_logging_level() -> LoggingLevels:
    """Get logging level from the env variable."""
    verbosity = ZENML_LOGGING_VERBOSITY.upper()
    if verbosity not in LoggingLevels.__members__:
        raise KeyError(
            f"Verbosity must be one of {list(LoggingLevels.__members__.keys())}"
        )
    return LoggingLevels[verbosity]


def set_root_verbosity() -> None:
    """Set the root verbosity."""
    level = get_logging_level()
    if level != LoggingLevels.NOTSET:
        if ENABLE_RICH_TRACEBACK:
            rich_tb_install(show_locals=(level == LoggingLevels.DEBUG))

        logging.basicConfig(level=level.value)
        get_logger(__name__).debug(
            f"Logging set to level: " f"{logging.getLevelName(level.value)}"
        )
    else:
        logging.disable(sys.maxsize)
        logging.getLogger().disabled = True
        get_logger(__name__).debug("Logging NOTSET")


def get_console_handler() -> Any:
    """Get console handler for logging."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    return console_handler
    # console_handler = RichHandler(
    #     show_path=False, omit_repeated_times=False, console=console
    # )
    # console_handler.setFormatter(CustomFormatter())
    # return console_handler


def get_file_handler() -> Any:
    """Return a file handler for logging."""
    file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight")
    file_handler.setFormatter(CustomFormatter())
    return file_handler


def get_logger(logger_name: str) -> logging.Logger:
    """Main function to get logger name,.

    Args:
      logger_name: Name of logger to initialize.

    Returns:
        A logger object.

    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(get_logging_level().value)
    logger.addHandler(get_console_handler())

    # TODO [ENG-130]: Add a file handler for persistent handling
    #  logger.addHandler(get_file_handler())
    #  with this pattern, it's rarely necessary to propagate the error up to
    #  parent
    logger.propagate = False
    return logger


def init_logging() -> None:
    """Initialize logging with default levels."""
    # Mute tensorflow cuda warnings
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    set_root_verbosity()

    # Enable logs if environment variable SUPRESS_ZENML_LOGS is not set to True
    supress_zenml_logs: bool = handle_bool_env_var(
        ENV_ZENML_SUPPRESS_LOGS, True
    )
    if supress_zenml_logs:
        # supress logger info messages
        supressed_logger_names = [
            "urllib3",
            "azure.core.pipeline.policies.http_logging_policy",
            "grpc",
            "requests",
            "kfp",
            "tensorflow",
        ]
        for logger_name in supressed_logger_names:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        # disable logger messages
        disabled_logger_names = [
            "apache_beam",
            "rdbms_metadata_access_object",
            "apache_beam.io.gcp.bigquery",
            "backoff",
            "segment",
        ]
        for logger_name in disabled_logger_names:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
            logging.getLogger(logger_name).disabled = True

    # set absl logging
    absl_logging.set_verbosity(ABSL_LOGGING_VERBOSITY)


@contextmanager
def disable_logging(log_level: int) -> Iterator[None]:
    """Contextmanager that temporarily disables logs below a threshold level.

    Use it like this:
    ```python
    with disable_logging(log_level=logging.INFO):
        # do something that shouldn't show DEBUG/INFO logs
        ...
    ```

    Args:
        log_level: All logs below this level will be disabled for the duration
            of this contextmanager.
    """
    old_level = logging.root.manager.disable
    try:
        logging.disable(log_level)
        yield
    finally:
        logging.disable(old_level)
