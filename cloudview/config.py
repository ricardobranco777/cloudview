"""
Helper functions
"""

import logging
import os
import stat
import sys
from pathlib import Path

import yaml

from cloudview.singleton import Singleton


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


@Singleton
class Config:
    """
    Read configuration
    """

    def __init__(self, path: Path, insecure: bool = False):
        self.path = path
        self.insecure = insecure
        self.config: dict = {}
        self.last_modified_time: float = float("Nan")

    def get_config(self) -> dict:
        """
        Get configuration from yaml
        """
        try:
            check_permissions(self.path, self.insecure)
            last_modified_time = self.path.stat().st_mtime

            # Check if the current modification time is different from the last one
            if self.last_modified_time == last_modified_time:
                return self.config

            # If the file has been modified, read the configuration
            with open(self.path, encoding="utf-8") as file:
                config = yaml.full_load(file)
        except OSError:
            if self.config:
                return self.config
            raise

        check_leafs(config, self.insecure)

        # Cache the configuration and modification time
        self.config = config
        self.last_modified_time = last_modified_time

        return config
