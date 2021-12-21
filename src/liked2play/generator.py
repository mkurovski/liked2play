"""
Music features Enrichment and Preprocessing
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"


import logging
import os

import numpy as np
import pandas as pd

_logger = logging.getLogger(__name__)


unscaled_attributes = ["key", "loudness", "tempo"]
scaled_attributes = [
    "mode",
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]


def generate_playlist(cfg: dict):
    filepath = os.path.join(cfg["interim_storage_folder"], "liked_songs_augmented.csv")
    _logger.info(f"Loading augmented raw features from {filepath} ...")
    liked_songs = pd.read_csv(filepath)

    not_listened = (liked_songs["count"] == 0).values
    weights = np.log1p(liked_songs["count"]).values.reshape(-1, 1)

    feature_cols = scaled_attributes + unscaled_attributes
    features = liked_songs[feature_cols].copy()

    # scale the unscaled features
    # assuming at least ordinal scale
    features["key"] = features["key"] / 11
    # TODO: improve beyond min-max-scaling
    features["loudness"] = -(features["loudness"] - features["loudness"].min()) / (
        features["loudness"].min() - features["loudness"].max()
    )
    features["tempo"] = (features["tempo"] - features["tempo"].min()) / (
        features["tempo"].max() - features["tempo"].min()
    )
    features = features.values

    # create
    user = (features * weights).sum(axis=0) / weights.sum().reshape(1, -1)
    similarities = (features * user).sum(axis=1) / (
        np.sqrt(np.sum(np.square(user))) * np.sqrt(np.sum(np.square(features), axis=1))
    )

    order = np.argsort(similarities)[::-1]
    order = [val for val in order if val in np.where(not_listened)[0]]
    if len(order) < cfg["top_k_songs"]:
        _logger.warning(
            f"Only {len(order)} songs remain, "
            f"requested {cfg['top_k_songs']} will not be fulfilled."
        )
    new_playlist = liked_songs.loc[order[: cfg["top_k_songs"]]]
    output_path = os.path.join(
        cfg["interim_storage_folder"], "recommended_playlist.csv"
    )
    _logger.info(f"Saving Playlist to {output_path} ...")
    new_playlist.to_csv(output_path, index=False)
