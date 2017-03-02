"""This module contains support functions for the application."""
from __future__ import print_function


def setting_globals(**kwargs):
    """Public global settings."""
    global VERBOSE
    VERBOSE = kwargs.get('verbose', False)


def v_print(content, **args):
    if VERBOSE:
        print(content, **args)
