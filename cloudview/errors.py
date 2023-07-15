#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Class for error & warning messages
"""

import logging
import sys
import traceback


def warning(msg, err):
    """
    Print warning message
    """
    if isinstance(err, Exception):
        logging.debug("%s", traceback.format_exc())
        err = f"{err.__class__.__name__}: {err}"
    logging.warning("%s: %s", msg, err)


def error(msg, err):
    """
    Print error message and exit
    """
    if isinstance(err, Exception):
        logging.debug("%s", traceback.format_exc())
        err = f"{err.__class__.__name__}: {err}"
    logging.error("%s: %s", msg, err)
    sys.exit(1)
