# Testing the Immich Slideshow Integration

This guide will help you test the Immich Home Assistant integration step by step.

## Prerequisites

1. **Immich Server**: You need a running Immich server with photos
2. **Home Assistant**: Running Home Assistant instance
3. **API Key**: Generated API key from your Immich user settings

## Step 1: Test Immich API Connection

Before installing the integration, test your Immich API connection:

```bash
python test_immich_api.py
```

This script will:
- Test connection to your Immich server
- List available albums
- Show sample images
- Verify API endpoints work correctly

**Expected output:**
```
✅ Connection successful!
✅ Found 5 albums
  1. Family Photos (ID: abc123)
  2. Vacation 2024 (ID: def456)
✅ Found 150 assets (showing first 10)
  1. IMG_001.jpg (IMAGE)
  2. IMG_002.jpg (IMAGE)
✅ Thumbnail URL accessible
```

## Step 2: Install the Integration

1. **Copy files** to Home Assistant:
   ```bash
   # Copy the entire immich_slideshow folder to:
   # <home_assistant_config>/custom_components/immich_slideshow/
   ```

2. **Restart Home Assistant**

3. **Add Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Immich Slideshow"
   - Enter your server details:
     - Server URL: `http://your-immich-server:2283`
     - API Key: Your generated API key
     - Album ID: (Optional) Specific album ID

## Step 3: Verify Integration Setup

After adding the integration, you should see these entities:

### Entities Created:
- `camera.immich_slideshow` - Camera showing current image
- `sensor.immich_current_image` - Current image details
- `sensor.immich_image_count` - Total number of images
- `sensor.immich_next_image` - Service entity for advancing images

### Check in Developer Tools:
1. Go to Developer Tools → States
2. Look for entities starting with `immich_slideshow`
3. Verify they have data and are not "unavailable"

## Step 4: Test Basic Functionality

### Test 1: Camera Entity
1. Go to Developer Tools → States
2. Find `camera.immich_slideshow`
3. Click the camera icon to view the image
4. **Expected**: Should display an image from your Immich library

### Test 2: Sensor Data
Check these sensors have correct data:
- `sensor.immich_current_image`: Should show current image ID
- `sensor.immich_image_count`: Should show total number of images
- Image attributes should include filename, URLs, etc.

### Test 3: Next Image Service
1. Go to Developer Tools → Services
2. Find service `immich_slideshow.next_image`
3. Call the service
4. **Expected**: Current image should change to next image

## Step 5: Test Lovelace Dashboard

Add test cards to your dashboard using `test_lovelace.yaml`:

### Basic Camera Card:
```yaml
- type: picture-entity
  entity: camera.immich_slideshow
  tap_action:
    action: call-service
    service: immich_slideshow.next_image
    target:
      entity_id: sensor.immich_next_image
```

### Test the card:
- **Expected**: Image displays correctly
- **Expected**: Tapping advances to next image

## Step 6: Test Automations

Add test automation from `test_configuration.yaml`:

```yaml
automation:
  - alias: "Immich Slideshow Auto Advance"
    trigger:
      - platform: time_pattern
        seconds: "/30"
    action:
      - service: immich_slideshow.next_image
        target:
          entity_id: sensor.immich_next_image
```

**Expected**: Images should automatically advance every 30 seconds

## Troubleshooting

### Common Issues:

#### 1. "Cannot Connect" Error
- **Check**: Server URL is correct and accessible
- **Check**: Immich server is running
- **Check**: No firewall blocking connection
- **Test**: Run `test_immich_api.py` script first

#### 2. "Invalid Auth" Error  
- **Check**: API key is correct
- **Check**: API key hasn't expired
- **Generate**: New API key in Immich user settings

#### 3. No Images Showing
- **Check**: Album has images (if album ID specified)
- **Check**: User has access to images
- **Check**: Images are not corrupted

#### 4. Images Not Loading
- **Check**: Network connectivity between HA and Immich
- **Check**: Image file sizes (very large images may timeout)
- **Try**: Using thumbnail URLs instead of full resolution

#### 5. Service Not Working
- **Check**: Entity IDs are correct in service calls
- **Check**: Integration loaded properly (check logs)
- **Restart**: Home Assistant if needed

### Debug Logs

Enable debug logging in Home Assistant:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.immich_slideshow: debug
```

Check logs in Settings → System → Logs

### Integration Status

Check integration status:
1. Go to Settings → Devices & Services
2. Find "Immich Slideshow" integration
3. Click on it to see device and entity status
4. All entities should be enabled and available

## Performance Testing

### Large Libraries:
- Test with libraries containing 1000+ images
- Monitor memory usage and response times
- Consider using album filters for better performance

### Network Performance:
- Test over local network vs internet connection
- Monitor image loading times
- Test with different image sizes/quality settings

## Success Criteria

✅ **Basic Connection**: API test script passes all checks  
✅ **Integration Setup**: All entities created and available  
✅ **Image Display**: Camera entity shows images correctly  
✅ **Service Function**: Next image service advances slideshow  
✅ **Automation**: Auto-advance works as expected  
✅ **Dashboard**: Lovelace cards display and function properly  

If all criteria pass, your Immich slideshow integration is working correctly!