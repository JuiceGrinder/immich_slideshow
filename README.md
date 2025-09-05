# Immich Slideshow Home Assistant Integration

A custom Home Assistant integration that displays pictures from your Immich server as a slideshow.

## Features

- **Camera Entity**: Display current image from Immich as a camera feed
- **Sensor Entities**: Track current image info, total image count
- **Service**: Advance to next image in slideshow
- **Album Support**: Display images from a specific album or all images
- **Auto-refresh**: Automatically cycles through images

## Installation

### Manual Installation

1. Download or clone this repository
2. Copy the entire `custom_components/immich_slideshow` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "Immich Slideshow" and follow the setup process

Your directory structure should look like:
```
config/
├── custom_components/
│   └── immich_slideshow/
│       ├── __init__.py
│       ├── manifest.json
│       ├── camera.py
│       ├── sensor.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── immich_client.py
│       ├── const.py
│       ├── services.yaml
│       └── strings.json
```

### HACS Installation (Future)

This integration is not yet available through HACS but may be added in the future.

### Configuration

You'll need the following information from your Immich server:

- **Server URL**: The URL of your Immich server (e.g., `http://192.168.1.100:2283`)
- **API Key**: Generate this in your Immich user settings
- **Album ID**: (Optional) Specific album ID to show images from. Leave empty to show all images.

## Usage

### Entities Created

After setup, the integration creates:

1. **Camera**: `camera.immich_slideshow`
   - Shows the current image
   - Attributes include image URL, filename, and position info

2. **Sensors**:
   - `sensor.immich_current_image`: Current image ID and metadata
   - `sensor.immich_image_count`: Total number of images available

### Services

- `immich_slideshow.next_image`: Advance to the next image in the slideshow

### Example Automation

```yaml
alias: "Immich Slideshow Auto Advance"
description: "Automatically advance slideshow every 30 seconds"
trigger:
  - platform: time_pattern
    seconds: "/30"
action:
  - service: immich_slideshow.next_image
    target:
      entity_id: sensor.immich_next_image
```

### Lovelace Card Example

```yaml
type: picture-entity
entity: camera.immich_slideshow
show_name: false
show_state: false
tap_action:
  action: call-service
  service: immich_slideshow.next_image
  target:
    entity_id: sensor.immich_next_image
```

## API Requirements

This integration uses the following Immich API endpoints:

- `/api/server/ping` - Connection testing
- `/api/albums` - Get albums list
- `/api/albums/{id}` - Get album assets
- `/api/assets/{id}/thumbnail` - Get image thumbnails
- `/api/assets/{id}/original` - Get full resolution images

**Note**: This integration requires Immich API version 1.139.3 or later with the updated endpoint structure.

## Troubleshooting

1. **Connection Issues**: Ensure your Immich server is accessible from Home Assistant and the API key is valid.
2. **No Images**: Check that your album has images or that there are images in your Immich library.
3. **Slow Loading**: Large images may take time to load. Consider using the thumbnail URL for faster display.

## Support

This is a community-developed integration. Please report issues and feature requests on the project repository.