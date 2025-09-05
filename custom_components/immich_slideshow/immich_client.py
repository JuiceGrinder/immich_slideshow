"""Immich API client."""
from __future__ import annotations

import logging
from typing import Any
import requests

_LOGGER = logging.getLogger(__name__)

class ImmichClient:
    """Client for interacting with Immich API."""

    def __init__(self, server_url: str, api_key: str) -> None:
        """Initialize the Immich client."""
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "x-api-key": api_key,
        }

    def test_connection(self) -> bool:
        """Test connection to Immich server."""
        try:
            response = requests.get(
                f"{self.server_url}/api/server/ping",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            _LOGGER.error("Failed to connect to Immich server: %s", exc)
            raise

    def get_albums(self) -> list[dict[str, Any]]:
        """Get list of albums."""
        try:
            response = requests.get(
                f"{self.server_url}/api/albums",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            _LOGGER.error("Failed to get albums: %s", exc)
            return []

    def get_album_assets(self, album_id: str | None = None) -> list[dict[str, Any]]:
        """Get assets from an album or all assets if no album specified."""
        try:
            if album_id:
                response = requests.get(
                    f"{self.server_url}/api/albums/{album_id}",
                    headers=self.headers,
                    timeout=30,  # Increased timeout for initial load
                )
                response.raise_for_status()
                album_data = response.json()
                return album_data.get("assets", [])
            else:
                response = requests.get(
                    f"{self.server_url}/api/assets",
                    headers=self.headers,
                    params={"size": 100},
                    timeout=30,  # Increased timeout for initial load
                )
                response.raise_for_status()
                return response.json()
        except requests.RequestException as exc:
            _LOGGER.error("Failed to get assets: %s", exc)
            return []

    def get_asset_thumbnail_url(self, asset_id: str, size: str = "preview") -> str:
        """Get thumbnail URL for an asset."""
        return f"{self.server_url}/api/assets/{asset_id}/thumbnail?size={size}"

    def get_asset_download_url(self, asset_id: str) -> str:
        """Get download URL for an asset."""
        return f"{self.server_url}/api/assets/{asset_id}/original"