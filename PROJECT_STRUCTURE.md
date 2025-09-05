# Project Structure

This document outlines the proper structure for the Immich Slideshow Home Assistant custom component.

## Directory Structure

```
immich_slideshow/
├── custom_components/
│   └── immich_slideshow/           # Main component directory
│       ├── __init__.py             # Component initialization
│       ├── manifest.json           # Component manifest
│       ├── camera.py              # Camera platform
│       ├── sensor.py              # Sensor platform
│       ├── config_flow.py         # Configuration flow
│       ├── coordinator.py         # Data update coordinator
│       ├── immich_client.py       # Immich API client
│       ├── const.py               # Constants
│       ├── services.yaml          # Service definitions
│       └── strings.json           # UI strings
├── docs/                          # Documentation
│   └── TESTING.md                 # Testing documentation
├── tests/                         # Test files
│   └── test_immich_api.py         # API testing script
├── examples/                      # Example configurations
│   ├── test_configuration.yaml    # Example HA config
│   └── test_lovelace.yaml         # Example Lovelace config
├── README.md                      # Main documentation
└── PROJECT_STRUCTURE.md           # This file
```

## Component Files Description

### Core Files

- **`__init__.py`**: Main component initialization, handles setup and teardown
- **`manifest.json`**: Defines component metadata, dependencies, and requirements
- **`const.py`**: Constants used throughout the component

### Platform Files

- **`camera.py`**: Implements the camera platform for displaying images
- **`sensor.py`**: Implements sensor platforms for image metadata

### Configuration

- **`config_flow.py`**: Handles the integration setup UI and validation
- **`strings.json`**: UI text strings for the configuration flow

### Data Management

- **`coordinator.py`**: Manages data updates and coordinates with Immich API
- **`immich_client.py`**: API client for communicating with Immich server

### Services

- **`services.yaml`**: Defines available services (e.g., next_image)

## Installation Structure

When properly installed, the component should be located at:
```
/config/custom_components/immich_slideshow/
```

This follows Home Assistant's standard custom component directory structure.

## Development Structure

For development and testing:

- **`tests/`**: Contains test scripts and utilities
- **`docs/`**: Additional documentation
- **`examples/`**: Sample configurations for users

## File Naming Conventions

- Snake_case for Python files
- Relative imports within the component (e.g., `from .const import DOMAIN`)
- Consistent naming for entities and services