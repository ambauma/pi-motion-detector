"""Define the command line interface"""
import argparse
import logging
import sys
from py_motion_detector import Watcher


def get_args():
    """Get args from sys."""
    return sys.argv[1:]

def init():
    """Initialize the arguments."""
    parser = argparse.ArgumentParser(
        prog="py-motion-detector",
        description='Watch for motion and capture an image of it.'
    )
    parser.add_argument('--log-cli-level',
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                        default="INFO",
                        help='set the log level')
    args = parser.parse_args(get_args())
    logging.basicConfig(level=getattr(logging, args.log_cli_level))
    with Watcher() as mw:
        while mw.continue_looping:
            mw.watch()
