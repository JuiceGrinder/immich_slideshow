#!/usr/bin/env python3
"""Test script to verify Immich API connectivity before installing the Home Assistant integration."""

import requests
import json
import sys
from typing import Optional

def test_immich_connection(server_url: str, api_key: str) -> bool:
    """Test basic connection to Immich server."""
    print(f"Testing connection to: {server_url}")
    
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    
    try:
        response = requests.get(
            f"{server_url.rstrip('/')}/api/server/ping",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        print("✅ Connection successful!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_get_albums(server_url: str, api_key: str) -> list:
    """Test getting albums from Immich."""
    print("\nTesting album retrieval...")
    
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    
    try:
        response = requests.get(
            f"{server_url.rstrip('/')}/api/albums",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        albums = response.json()
        print(f"✅ Found {len(albums)} albums")
        
        for i, album in enumerate(albums[:5]):  # Show first 5 albums
            print(f"  {i+1}. {album.get('albumName', 'Unnamed')} (ID: {album.get('id', 'Unknown')})")
        
        if len(albums) > 5:
            print(f"  ... and {len(albums) - 5} more albums")
            
        return albums
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get albums: {e}")
        return []

def test_get_assets(server_url: str, api_key: str, album_id: Optional[str] = None) -> list:
    """Test getting assets from Immich."""
    if album_id:
        print(f"\nTesting asset retrieval from album {album_id}...")
        endpoint = f"{server_url.rstrip('/')}/api/albums/{album_id}"
    else:
        print("\nTesting asset retrieval (using first album with assets)...")
        # Get all albums first and use one with assets
        albums_response = requests.get(
            f"{server_url.rstrip('/')}/api/albums",
            headers={"Accept": "application/json", "x-api-key": api_key},
            timeout=10,
        )
        albums_response.raise_for_status()
        albums = albums_response.json()
        
        # Find an album with assets
        album_with_assets = None
        for album in albums:
            if album.get('assetCount', 0) > 0:
                album_with_assets = album
                break
        
        if not album_with_assets:
            print("❌ No albums with assets found")
            return []
        
        endpoint = f"{server_url.rstrip('/')}/api/albums/{album_with_assets['id']}"
        print(f"Using album: {album_with_assets['albumName']} ({album_with_assets['assetCount']} assets)")
    
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    
    try:
        response = requests.get(
            endpoint,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        
        album_data = response.json()
        assets = album_data.get("assets", [])
        print(f"✅ Album contains {len(assets)} assets")
        
        for i, asset in enumerate(assets[:3]):  # Show first 3 assets
            filename = asset.get('originalFileName', 'Unknown')
            asset_type = asset.get('type', 'Unknown')
            print(f"  {i+1}. {filename} ({asset_type})")
            
        return assets
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get assets: {e}")
        return []

def test_image_urls(server_url: str, api_key: str, asset_id: str):
    """Test image URL generation."""
    print(f"\nTesting image URLs for asset {asset_id}...")
    
    thumbnail_url = f"{server_url.rstrip('/')}/api/assets/{asset_id}/thumbnail"
    download_url = f"{server_url.rstrip('/')}/api/assets/{asset_id}/original"
    
    print(f"Thumbnail URL: {thumbnail_url}")
    print(f"Download URL: {download_url}")
    
    # Test thumbnail access
    try:
        headers = {"x-api-key": api_key}
        response = requests.head(thumbnail_url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Thumbnail URL accessible")
        else:
            print(f"⚠️  Thumbnail URL returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Thumbnail URL test failed: {e}")

def main():
    """Main test function."""
    print("Immich API Test Script")
    print("=" * 50)
    
    # Try to use values from const.py first
    try:
        from const import CONF_SERVER_URL, CONF_API_KEY, CONF_ALBUM_ID
        server_url = CONF_SERVER_URL
        api_key = CONF_API_KEY
        album_id = CONF_ALBUM_ID if CONF_ALBUM_ID != "Construction" else None
        
        print(f"Using configuration from const.py:")
        print(f"  Server URL: {server_url}")
        print(f"  API Key: {api_key[:10]}...{api_key[-10:]}")
        print(f"  Album ID: {album_id}")
        print()
    except ImportError:
        # Fallback to user input
        server_url = input("Enter your Immich server URL (e.g., http://192.168.1.100:2283): ").strip()
        api_key = input("Enter your Immich API key: ").strip()
        album_id = None
        
        if not server_url or not api_key:
            print("❌ Server URL and API key are required!")
            sys.exit(1)
    
    # Test connection
    print("Starting API tests...")
    if not test_immich_connection(server_url, api_key):
        sys.exit(1)
    
    # Test albums
    albums = test_get_albums(server_url, api_key)
    
    # Test assets with specific album if provided
    if album_id and albums:
        # Check if album_id is an actual ID or a name
        target_album_id = None
        album_name = None
        
        # First check if it's a direct ID match
        for album in albums:
            if album.get('id') == album_id:
                target_album_id = album_id
                album_name = album.get('albumName', 'Unknown')
                break
        
        # If not found by ID, try matching by name
        if not target_album_id:
            for album in albums:
                if album.get('albumName', '').lower() == album_id.lower():
                    target_album_id = album.get('id')
                    album_name = album.get('albumName')
                    break
        
        if target_album_id:
            print(f"\nFound album: {album_name} (ID: {target_album_id})")
            assets = test_get_assets(server_url, api_key, target_album_id)
        else:
            print(f"\nAlbum {album_id} not found, testing with first available album...")
            assets = test_get_assets(server_url, api_key)
    else:
        print("\nTesting with first available album...")
        assets = test_get_assets(server_url, api_key)
    
    # Test image URLs if we have assets
    if assets:
        test_image_urls(server_url, api_key, assets[0]['id'])
    else:
        print("⚠️  No assets found to test image URLs")
    
    print("\n" + "=" * 50)
    if assets:
        print("✅ API tests completed successfully!")
        print("\nYour Immich server is ready for the Home Assistant integration.")
    else:
        print("⚠️  API connection works but no images found.")
        print("Make sure you have images in your Immich library or specified album.")
    
    print(f"\nConfiguration for Home Assistant:")
    print(f"  Server URL: {server_url}")
    print(f"  API Key: {api_key}")
    if album_id:
        print(f"  Album ID: {album_id}")

if __name__ == "__main__":
    main()