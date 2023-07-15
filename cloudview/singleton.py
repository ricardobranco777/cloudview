#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Singleton decorator
"""

import functools


class Singleton:  # pylint: disable=too-few-public-methods
    """
    Singleton decorator
    """

    def __init__(self, cls):
        self.cls = cls
        self.instance = None
        functools.update_wrapper(self, cls)

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance



class Singleton2:  # pylint: disable=too-few-public-methods
    """
    Singleton decorator
    """

    def __init__(self, cls):
        self.cls = cls
        self.instances = {}
        functools.update_wrapper(self, cls)

    def __call__(self, *args, **kwargs):
        key = (self.cls, args, frozenset(kwargs.items()))
        if key not in self.instances:
            self.instances[key] = self.cls(*args, **kwargs)
        return self.instances[key]
