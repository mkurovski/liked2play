"""
Music features Enrichment and Preprocessing
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"


import logging
import os

import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .utils import load_credentials

_logger = logging.getLogger(__name__)


# During the process you are redirected to the URL, copy it and put it into the request
def upload_playlist(cfg: dict):
    filepath = os.path.join(cfg["interim_storage_folder"], "recommended_playlist.csv")
    playlist = pd.read_csv(filepath)

    # use spotipy to create connection
    credentials = load_credentials(cfg)
    scope = "playlist-modify-public"

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=cfg["redirect_url"],
            scope=scope,
        )
    )

    res = sp.user_playlist_create(
        user=credentials["user_id"],
        name=cfg["playlist_name"],
        description=cfg["description"],
    )
    playlist_id = res["id"]
    sp.playlist_add_items(playlist_id, playlist["uri"].tolist())
    _logger.info(
        f"Successfully created playlist {cfg['playlist_name']} with id {playlist_id}."
    )
