"""
Music features Enrichment and Preprocessing
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"


import json
import logging
import os
import time
from collections import Counter
from typing import List

import pandas as pd
import requests

from .analysis import read_liked_songs, read_streaming_history
from .utils import get_access_token, load_credentials

_logger = logging.getLogger(__name__)


def preprocess_music_data(cfg: dict):
    folderpath = cfg["gdpr_data_path"]
    liked_songs = read_liked_songs(folderpath)
    # test mode
    liked_songs = liked_songs.iloc[:200]
    streamed_songs = read_streaming_history(folderpath)
    streamed_songs = streamed_songs[streamed_songs["msPlayed"] >= cfg["play_threshold"]]

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

    # Check on Liking Behavior
    liked_songs["id"] = liked_songs["uri"].apply(lambda val: val.split(":")[-1])
    liked_songs["artist_track"] = [
        a + ": " + b
        for a, b in zip(liked_songs["artist"].values, liked_songs["track"].values)
    ]

    track_ids = liked_songs["id"].values.tolist()
    audio_features = fetch_audio_features(track_ids, cfg)

    liked_songs = liked_songs.merge(
        play_counts, how="left", left_on="artist_track", right_on="track"
    )
    liked_songs["count"] = liked_songs["count"].fillna(0)
    liked_songs = liked_songs.merge(
        audio_features.drop(columns="id"), how="left", on="uri"
    )

    filepath = os.path.join(
        cfg["interim_storage_folder"], "TEST_liked_songs_augmented.csv"
    )
    _logger.info(f"Saving augmented liked songs to {filepath}")
    liked_songs.to_csv(filepath, index=False)


def fetch_audio_features(
    ids: List[str],
    cfg: dict,
    batch_size: int = 100,
    sleep_seconds_between_batches: int = 5,
) -> pd.DataFrame:
    credentials = load_credentials(cfg)
    token = get_access_token(credentials["client_id"], credentials["client_secret"])
    headers = {"Authorization": "Bearer " + token}

    base_url = "https://api.spotify.com"
    endpoint = "/v1/audio-features"
    url = f"{base_url}{endpoint}"

    results = list()
    for idx in range(0, len(ids), batch_size):
        batch_ids = ids[idx : idx + batch_size]
        params = {"ids": ",".join(batch_ids)}
        _logger.info(
            f"Requesting Audio Features for Batch "
            f"[{idx}:{idx + batch_size}] / {len(ids)} ..."
        )
        res = requests.get(url=url, headers=headers, params=params)
        res = json.loads(res.content)["audio_features"]
        assert len(batch_ids) == len(res)
        results.extend(res)

        time.sleep(sleep_seconds_between_batches)

    audio_features = pd.DataFrame(results)
    audio_features.index = ids

    return audio_features
