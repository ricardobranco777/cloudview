"""
CachedFile reads a file only if it was modified
"""

import logging
import os

from cloudview.singleton import Singleton2


class CachedFile(metaclass=Singleton2):  # pylint: disable=too-few-public-methods
    """
    CachedFile reads a text file only if data or metadata was modified
    """

    __slots__ = ("path", "data", "metadata")

    def __init__(self, path: str):
        self.path = path
        with open(self.path, encoding="utf-8") as file:
            self.metadata = os.fstat(file.fileno())
            self.data = file.read()

    def __repr__(self):
        return f'{type(self).__name__}(path="self.path")'

    def get_data(self) -> str:
        """
        Get data and save metadata
        """
        try:
            metadata = os.stat(self.path)
            if metadata.st_mtime != self.metadata.st_mtime:
                with open(self.path, encoding="utf-8") as file:
                    self.data = file.read()
                self.metadata = metadata
        except OSError as exc:
            logging.warning("%s: %s", self.path, exc)
        return self.data
