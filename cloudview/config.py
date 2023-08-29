"""
Helper functions
"""

import logging
import os
import stat
import sys
from pathlib import Path

import yaml

from cloudview.singleton import Singleton2


def check_permissions(path: Path, insecure: bool = False) -> None:
    """
    Check file permissions
    """
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        if insecure:
            logging.warning("%s is world readable", path)
        else:
            logging.error("%s is world readable", path)
            sys.exit(1)


def check_leafs(tree: dict, insecure: bool = False) -> None:
    """
    Check a nested dict for string values containing files and check permissions
    """
    for value in tree.values():
        if isinstance(value, dict):
            check_leafs(value)
        elif isinstance(value, str):
            try:
                if os.path.isabs(value) and os.path.isfile(value):
                    check_permissions(Path(value), insecure)
            except OSError:
                pass


class Config(metaclass=Singleton2):
    """
    Read configuration
    """

    def __init__(self, path: Path, insecure: bool = False):
        self._path = path
        self._insecure = insecure
        self._config: dict = {}
        self._last_modified_time: float = float("Nan")

    def __repr__(self):
        return f"{type(self).__name__}(path={self._path}, insecure={self._insecure})"

    def get_config(self) -> dict:
        """
        Get configuration from yaml
        """
        try:
            check_permissions(self._path, self._insecure)
            last_modified_time = self._path.stat().st_mtime

            # Check if the current modification time is different from the last one
            if self._last_modified_time == last_modified_time:
                return self._config

            # If the file has been modified, read the configuration
            with open(self._path, encoding="utf-8") as file:
                config = yaml.full_load(file)
        except OSError:
            if self._config:
                return self._config
            raise

        check_leafs(config, self._insecure)

        # Cache the configuration and modification time
        self._config = config
        self._last_modified_time = last_modified_time

        return config
