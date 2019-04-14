"""
Class for handling exceptions
"""

import logging
import sys
import traceback


class FatalError(Exception):
    """
    Class for handling exceptions
    """
    def __init__(self, msg, err):
        super().__init__(err)
        logger = logging.getLogger(__name__)
        if isinstance(err, Exception):
            err = "%s: %s" % (err.__class__.__name__, err)
            logger.debug("%s", traceback.format_exc())
        logger.error("%s: %s", msg, err)
        sys.exit(1)
