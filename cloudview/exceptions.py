"""
Class for handling exceptions
"""

import logging
import sys
import traceback


class MyException(Exception):
    """
    Class for handling exceptions
    """
    def __init__(self, err):
        super().__init__(err)
        if isinstance(err, Exception):
            err = "%s: %s" % (err.__class__.__name__, err)
            logging.debug("%s", traceback.format_exc())


class WarningError(MyException):
    """
    Class for handling warning exceptions
    """
    def __init__(self, msg, err):
        super().__init__(err)
        logging.warning("%s: %s", msg, err)


class FatalError(MyException):
    """
    Class for handling fatal exceptions
    """
    def __init__(self, msg, err):
        super().__init__(err)
        logging.error("%s: %s", msg, err)
        sys.exit(1)
