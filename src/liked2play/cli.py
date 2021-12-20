"""
Generator Script to Orchestrate the Playlist Generation Steps
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"


import argparse
import json
import logging
import os
import sys

from .analysis import analyze_gdpr_data
from .features import preprocess_music_data
from .generator import generate_playlist
from .uploader import upload_playlist

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_args(args):
    """Parse command line parameters
    Args:
      args ([str]): command line parameters as list of strings
    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Playlist Generator")
    parser.add_argument(
        "-m",
        "--mode",
        dest="mode",
        help="Mode can be Data Analysis, Feature Preprocessing,"
        "Playlist Generation, or Upload",
        type=str,
        choices=["analyze", "preprocess", "generate", "upload", "end2end"],
        metavar="STR",
        required=True,
    )
    parser.add_argument(
        "-c",
        dest="config_filepath",
        help="Config File with all information",
        type=str,
        metavar="STR",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )

    return parser.parse_args(args)


def validate_config(cfg: dict):
    assert cfg["play_threshold"] >= 0

    gdpr_sar_filenames = os.listdir(cfg["gdpr_data_path"])
    assert "StreamingHistory0.json" in gdpr_sar_filenames
    assert "YourLibrary.json" in gdpr_sar_filenames

    assert os.path.exists(cfg["interim_storage_folder"])

    assert os.path.isfile(cfg["client_id_path"])
    assert os.path.isfile(cfg["client_secret_path"])


def run():
    """Entry point for console_scripts"""
    args = parse_args(sys.argv[1:])
    setup_logging(args.loglevel)

    with open(args.config_filepath, "rb") as file:
        config = json.load(file)

    validate_config(config)
    _logger.info(f"Config looks good - proceeding with mode: `{args.mode}`")

    if args.mode == "analyze":
        analyze_gdpr_data(config)
    elif args.mode == "preprocess":
        preprocess_music_data(config)
    elif args.mode == "generate":
        generate_playlist(config)
    elif args.mode == "upload":
        upload_playlist(config)
    elif args.mode == "end2end":
        preprocess_music_data(config)
        generate_playlist(config)
        upload_playlist(config)


if __name__ == "__main__":
    run()
