# -*- coding: utf-8 -*-

"""
Add logging capabilities to tx-client.
"""

import sys
import logging

_logger = logging.getLogger('txclib')
_logger.setLevel(logging.INFO)

_error_handler = logging.StreamHandler(sys.stderr)
_error_handler.setLevel(logging.WARNING)
_error_formatter = logging.Formatter('%(levelname)s: %(message)s')
_error_handler.setFormatter(_error_formatter)
_logger.addHandler(_error_handler)

_msg_handler = logging.StreamHandler(sys.stdout)
_msg_handler.setLevel(logging.DEBUG)
_msg_formatter = logging.Formatter('%(message)s')
_msg_handler.setFormatter(_msg_formatter)
_logger.addHandler(_msg_handler)

logger = _logger


def set_level(level):
    """Set the level for the logger.

    Args:
        level: A string among DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    logger.setLevel(getattr(logging, level))
