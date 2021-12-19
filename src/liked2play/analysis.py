"""
Analysis of Streaming History and Liked Songs
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"


import json
import logging
import os
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd

_logger = logging.getLogger(__name__)


# copied from numpyencoder: https://github.com/hmallen/numpyencoder
class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):

            return int(obj)

        return json.JSONEncoder.default(self, obj)


# Sort into preprocessing and analysis steps
def analyze_gdpr_data(cfg: dict, topn: int = 5) -> dict:
    report = dict()

    folderpath = cfg["gdpr_data_path"]
    liked_songs = read_liked_songs(folderpath)
    streamed_songs = read_streaming_history(folderpath)

    # Check on Streaming Behavior
    report["number_of_streamed_songs"] = streamed_songs.shape[0]
    report["period_start"] = streamed_songs["endTime"].min()
    report["period_end"] = streamed_songs["endTime"].max()

    # filter for played songs
    streamed_songs = streamed_songs[streamed_songs["msPlayed"] >= cfg["play_threshold"]]
    report["number_of_played_songs"] = streamed_songs.shape[0]
    report["stream_to_listen_conversion"] = round(
        report["number_of_played_songs"] / report["number_of_streamed_songs"], 4
    )

    # Determine Play Counts: filter and count
    counter = Counter(
        [
            a + ": " + b
            for a, b in zip(
                streamed_songs["artistName"].values, streamed_songs["trackName"].values
            )
        ]
    )
    play_counts = pd.DataFrame(counter.most_common(), columns=["track", "count"])

    report["top_artists_played"] = (
        streamed_songs["artistName"].value_counts().iloc[:topn].to_dict()
    )
    report["top_songs_played"] = play_counts.iloc[:topn].to_dict()

    # Check on Liking Behavior
    liked_songs["id"] = liked_songs["uri"].apply(lambda val: val.split(":")[-1])
    liked_songs["artist_track"] = [
        a + ": " + b
        for a, b in zip(liked_songs["artist"].values, liked_songs["track"].values)
    ]
    report["top_artists_liked"] = (
        liked_songs["artist"].value_counts().iloc[:topn].to_dict()
    )
    # assume that ea. track in liked songs is just there once

    # Check on Joint Insights: Streaming x Liking
    liked_songs = liked_songs.merge(
        play_counts, how="left", left_on="artist_track", right_on="track"
    )
    liked_songs["count"] = liked_songs["count"].fillna(0)
    report["count"] = liked_songs.shape[0]
    report["listened"] = (liked_songs["count"] != 0).sum()
    report["not_listened"] = liked_songs.shape[0] - report["listened"]
    report["not_listened_share"] = round(report["not_listened"] / report["count"], 4)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = os.path.join(
        cfg["interim_storage_folder"], f"{timestamp}_analysis_report.json"
    )
    with open(filepath, "w") as file:
        json.dump(report, file, indent=4, cls=NumpyEncoder)
    _logger.info("Liked and Streamed Tracks Report Generated:")
    _logger.info(json.dumps(report, indent=4, sort_keys=False, cls=NumpyEncoder))
    _logger.info(f"Report Persisted to {filepath}")


def read_streaming_history(folderpath: str) -> pd.DataFrame:
    streamed_songs = list()

    for filename in os.listdir(folderpath):
        if filename.startswith("StreamingHistory"):
            with open(os.path.join(folderpath, filename)) as file:
                streamed_songs.extend(json.load(file))

    streamed_songs = pd.DataFrame(streamed_songs)

    return streamed_songs


def read_liked_songs(folderpath: str) -> pd.DataFrame:
    with open(os.path.join(folderpath, "YourLibrary.json")) as file:
        liked_songs = json.load(file)["tracks"]
        liked_songs = pd.DataFrame(liked_songs)

    return liked_songs
