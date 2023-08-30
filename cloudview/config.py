"""
Helper functions
"""

import os
import stat

import yaml

from cloudview.cachedfile import CachedFile


def check_leafs(tree: dict) -> None:
    """
    Check a nested dict for string values containing files and check permissions
    """
    for value in tree.values():
        if isinstance(value, dict):
            check_leafs(value)
        elif isinstance(value, str):
            if os.path.isabs(value) and os.path.isfile(value):
                if os.stat(value).st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                    raise RuntimeError(f"{value} is group/world readable")


class Config(CachedFile):
    """
    Read configuration
    """

    def __init__(self, path: str):
        super().__init__(path)
        if self.metadata.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(f"{self.path} is group/world readable")

    def get_config(self) -> dict:
        """
        Get configuration from yaml
        """
        config = yaml.full_load(self.get_data())
        if self.metadata.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(f"{self.path} is group/world readable")
        check_leafs(config)
        return config
