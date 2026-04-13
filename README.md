# Home Assistant YAML Corrector Addon

A Home Assistant addon that validates and auto-corrects deprecated YAML syntax with dynamically updated deprecation rules.

## Features

✅ **Dynamic Deprecation Database**
- Fetches from multiple sources automatically
- Home Assistant GitHub releases
- Breaking changes documentation
- Core deprecation notices
- Common pattern library

✅ **Smart Validation**
- YAML syntax checking
- Deprecated pattern detection
- Automatic corrections
- Contextual suggestions

✅ **Background Sync**
- Scheduled updates (configurable interval)
- Caches data locally
- Respects GitHub rate limits
- Optional GitHub token for higher limits

✅ **Web Interface**
- Beautiful, intuitive dashboard
- Real-time validation
- Auto-fix functionality
- Deprecation rule viewer
- Status monitoring

## Installation

### Option 1: Add Custom Repository

1. Go to **Settings** → **Add-ons & Integrations** → **Add-ons**
2. Click **Create New Add-on Repository**
3. Enter repository URL: `https://github.com/YOUR_REPO/ha-addons`
4. Click **Create**
5. Find "Home Assistant YAML Corrector" and click **Install**

### Option 2: Manual Installation

1. SSH into your Home Assistant system
2. Navigate to add-ons directory:
   ```bash
   cd /addons
   ```
3. Clone the addon:
   ```bash
   git clone https://github.com/YOUR_REPO/ha-yaml-corrector ha-yaml-corrector
   ```
4. Go to **Settings** → **Add-ons & Integrations** → **Add-ons**
5. Click **⋮** → **Reload Add-ons**
6. Find "Home Assistant YAML Corrector" and click **Install**

## Configuration

### Default Options

```yaml
sync_interval: 360          # Minutes between sync operations (1-24 hours)
github_token: ""            # Optional GitHub token for higher rate limits
log_level: info             # Logging level: debug, info, warning, error
max_cache_age: 86400        # Seconds to cache data (1-7 days)
```

### GitHub Token (Optional)

To use your own GitHub token for higher API rate limits:

1. Create a GitHub Personal Access Token:
   - Go to **Settings** → **Developer settings** → **Personal access tokens**
   - Click **Generate new token**
   - Select `public_repo` scope
   - Copy the token

2. In the addon configuration, paste your token in the `github_token` field

3. Restart the addon

## Usage

### Accessing the Web Interface

1. Open Home Assistant
2. Go to **Settings** → **Add-ons & Integrations** → **Add-ons**
3. Find "Home Assistant YAML Corrector"
4. Click **Open web UI** button

Or access directly at: `http://homeassistant.local:8080`

### Validating YAML

1. **Upload or Paste**: Upload a YAML file or paste your configuration
2. **Click Validate**: Check for syntax errors and deprecated patterns
3. **Review Issues**: See detailed descriptions and suggestions
4. **Auto-Fix**: Click to automatically fix common issues
5. **Copy Output**: Copy the corrected YAML back to your config

### Understanding Issues

- **❌ Errors**: Critical syntax issues that will break your configuration
- **⚠️ Warnings**: Non-critical issues that might cause problems
- **🔄 Deprecated**: Old syntax that still works but should be updated

### Manual Sync

Click the "🔄 Sync Rules" button to manually fetch the latest deprecation rules from:
- GitHub releases
- HA documentation
- Core deprecations
- Common patterns

## API Endpoints

The addon exposes a REST API for integration with other tools:

### GET /api/health
Health check endpoint
```bash
curl http://homeassistant.local:8080/api/health
```

### GET /api/deprecations
Get current deprecation rules
```bash
curl http://homeassistant.local:8080/api/deprecations
```

### POST /api/validate
Validate YAML against deprecation rules
```bash
curl -X POST http://homeassistant.local:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{"yaml": "your yaml content here"}'
```

### POST /api/sync
Manually trigger deprecation sync
```bash
curl -X POST http://homeassistant.local:8080/api/sync
```

### GET /api/status
Get addon status and information
```bash
curl http://homeassistant.local:8080/api/status
```

## Common Deprecations Detected

### Sensors
- `platform: rest` → Use rest_sensor or rest_command
- `platform: command_line` → Use command or system_health
- `attribute:` → `attributes:` (singular to plural)

### Automations
- `trigger: sun` → `trigger: sun.sun` (requires explicit entity)
- `condition: template` → Restructured format
- `actions:` → `action:` (plural to singular)

### YAML Structure
- Indentation checks (2 or 4 spaces)
- Quote validation
- List format verification

## Logs

View addon logs in Home Assistant:
1. Go to **Settings** → **Add-ons & Integrations** → **Add-ons**
2. Find "Home Assistant YAML Corrector"
3. Click **Logs**

Or via command line:
```bash
docker logs addon_ha-yaml-corrector
```

## Troubleshooting

### Addon won't start
1. Check the logs for errors
2. Ensure you have enough disk space
3. Try restarting from the addon page

### Deprecation rules not updating
1. Check network connectivity
2. Verify GitHub rate limits (use GitHub token if needed)
3. Click "Sync Rules" button manually
4. Check logs for sync errors

### YAML validation not working
1. Ensure YAML is properly formatted
2. Check that input is not empty
3. Clear browser cache if issues persist

### High memory usage
1. Reduce `max_cache_age` to clean cache more frequently
2. Reduce `sync_interval` if updates are less important
3. Restart the addon

## Performance Notes

- Initial sync takes ~30 seconds depending on network
- Subsequent syncs are faster with caching
- Web interface is cached in browser for faster access
- API calls are typically <500ms

## Updates

The addon will notify you of updates in the Home Assistant UI. Simply click "Update" to get the latest deprecation detection capabilities.

## Contributing

Found an issue or want to improve the addon? Please open an issue on GitHub!

## Support

For issues and questions:
1. Check the logs first
2. Review the troubleshooting section
3. Open an issue on GitHub with:
   - Log output
   - Your HA version
   - Steps to reproduce

## License

MIT License - See LICENSE file for details
"# ha-addons" 
