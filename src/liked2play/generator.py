"""
Music features Enrichment and Preprocessing
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"

# finish module before 02:15
# finish the upload module before 02:30
import logging
import os

import numpy as np
import pandas as pd

_logger = logging.getLogger(__name__)


unscaled_attributes = ["key", "loudness", "mode", "tempo"]
# TODO: Move mode to scaled attributes possibly
scaled_attributes = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]


def generate_playlist(cfg: dict):
    filepath = os.path.join(
        cfg["interim_storage_folder"], "TEST_liked_songs_augmented.csv"
    )
    _logger.info(f"Loading augmented raw features from {filepath} ...")
    liked_songs = pd.read_csv(filepath)

    not_listened = (liked_songs["count"] == 0).values
    weights = np.log1p(liked_songs["count"]).values.reshape(-1, 1)

    feature_cols = scaled_attributes + unscaled_attributes
    features = liked_songs[feature_cols].copy()

    # scale the unscaled features
    # TODO: also check feature transformations for sclaed attributes
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
    # TODO: Check if number of songs can be fulfilled or not
    new_playlist = liked_songs.loc[order[: cfg["top_k_songs"]]]
    output_path = os.path.join(
        cfg["interim_storage_folder"], "recommended_playlist.csv"
    )
    _logger.info(f"Saving Playlist to {output_path} ...")
    new_playlist.to_csv(output_path, index=False)
