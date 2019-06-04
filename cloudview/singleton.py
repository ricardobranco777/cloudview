"""
Singleton decorator
"""


class Singleton:  # pylint: disable=too-few-public-methods
    """
    Singleton decorator
    """

    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance
