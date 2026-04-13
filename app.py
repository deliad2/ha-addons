import os
import json
import logging
import requests
import yaml
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Setup logging
log_level = os.getenv('LOG_LEVEL', 'info').upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Configuration
CACHE_DIR = Path('/data/deprecations')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / 'deprecations.json'
LAST_SYNC_FILE = CACHE_DIR / 'last_sync.json'
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 360))  # minutes
MAX_CACHE_AGE = int(os.getenv('MAX_CACHE_AGE', 86400))  # seconds
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

GITHUB_API = 'https://api.github.com'
HA_REPO = 'home-assistant/core'
HA_DOCS_REPO = 'home-assistant/home-assistant.io'

class DeprecationManager:
    def __init__(self):
        self.deprecations = self._load_cache()
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'HA-YAML-Corrector'
        }
        if GITHUB_TOKEN:
            self.headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    def _load_cache(self):
        """Load cached deprecations from disk"""
        if CACHE_FILE.exists():
            try:
                age = datetime.now() - datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
                if age.total_seconds() < MAX_CACHE_AGE:
                    with open(CACHE_FILE, 'r') as f:
                        return json.load(f)
                else:
                    logger.info("Cache expired, will refresh on next sync")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        
        return {'rules': [], 'last_updated': None, 'sources': []}
    
    def _save_cache(self):
        """Save deprecations to disk"""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.deprecations, f, indent=2)
            logger.info("Deprecations cached successfully")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _fetch_github_releases(self):
        """Fetch breaking changes from GitHub releases"""
        rules = []
        try:
            logger.info("Fetching GitHub releases...")
            url = f'{GITHUB_API}/repos/{HA_REPO}/releases'
            page = 1
            processed = 0
            
            while processed < 20:  # Limit to 20 releases
                response = requests.get(
                    f'{url}?page={page}&per_page=5',
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                releases = response.json()
                
                if not releases:
                    break
                
                for release in releases:
                    if release['draft'] or release['prerelease']:
                        continue
                    
                    body = release.get('body', '')
                    version = release['tag_name']
                    
                    # Parse breaking changes section
                    if '## Breaking Changes' in body or '### Breaking Changes' in body:
                        lines = body.split('\n')
                        in_breaking = False
                        for line in lines:
                            if 'Breaking Changes' in line:
                                in_breaking = True
                                continue
                            if in_breaking and line.startswith('##'):
                                break
                            if in_breaking and line.strip():
                                rules.append({
                                    'version': version,
                                    'type': 'breaking_change',
                                    'description': line.strip(),
                                    'source': 'github_releases'
                                })
                    processed += 1
                page += 1
            
            logger.info(f"Found {len(rules)} breaking changes from releases")
        except Exception as e:
            logger.error(f"Error fetching GitHub releases: {e}")
        
        return rules
    
    def _fetch_breaking_changes_doc(self):
        """Fetch deprecations from breaking-changes.md documentation"""
        rules = []
        try:
            logger.info("Fetching breaking changes documentation...")
            url = f'https://raw.githubusercontent.com/{HA_DOCS_REPO}/master/source/_docs/breaking_changes.markdown'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            lines = content.split('\n')
            
            current_version = None
            for i, line in enumerate(lines):
                # Version headers
                if line.startswith('## '):
                    current_version = line.replace('## ', '').strip()
                
                # Parse deprecation patterns
                if line.startswith('- **') and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        old_syntax = parts[0].replace('- **', '').replace('**', '').strip()
                        description = parts[1].strip()
                        rules.append({
                            'version': current_version,
                            'type': 'syntax_change',
                            'old_syntax': old_syntax,
                            'description': description,
                            'source': 'breaking_changes_doc'
                        })
            
            logger.info(f"Found {len(rules)} changes from documentation")
        except Exception as e:
            logger.error(f"Error fetching breaking changes doc: {e}")
        
        return rules
    
    def _fetch_platform_changes(self):
        """Fetch deprecated platforms and integrations from HA core"""
        rules = []
        try:
            logger.info("Fetching platform deprecations...")
            # Fetch from HA core deprecation notices
            url = f'https://raw.githubusercontent.com/{HA_REPO}/dev/homeassistant/deprecated.py'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            
            # Parse deprecated platforms
            deprecated_platforms = []
            for line in content.split('\n'):
                if 'DEPRECATED_' in line or 'deprecated' in line.lower():
                    if '=' in line:
                        rules.append({
                            'type': 'deprecated_platform',
                            'description': line.strip(),
                            'source': 'core_deprecated'
                        })
            
            logger.info(f"Found {len(rules)} platform deprecations")
        except Exception as e:
            logger.error(f"Error fetching platform changes: {e}")
        
        return rules
    
    def _parse_common_patterns(self):
        """Define common HA deprecation patterns"""
        return [
            {
                'type': 'sensor_platform',
                'old_pattern': 'platform: rest',
                'new_pattern': 'platform: rest_sensor or rest_command',
                'description': 'rest sensor platform deprecated',
                'source': 'common_patterns'
            },
            {
                'type': 'attribute_syntax',
                'old_pattern': 'attribute:',
                'new_pattern': 'attributes:',
                'description': 'Singular attribute changed to plural',
                'source': 'common_patterns'
            },
            {
                'type': 'action_syntax',
                'old_pattern': 'actions:',
                'new_pattern': 'action:',
                'description': 'Plural actions changed to singular',
                'source': 'common_patterns'
            },
            {
                'type': 'trigger_sun',
                'old_pattern': 'trigger: sun',
                'new_pattern': 'trigger: sun.sun or specify platform',
                'description': 'Sun trigger requires explicit entity',
                'source': 'common_patterns'
            },
            {
                'type': 'template_condition',
                'old_pattern': 'condition: template with value_template:',
                'new_pattern': 'Restructured condition format',
                'description': 'Template condition syntax changed',
                'source': 'common_patterns'
            }
        ]
    
    def sync(self):
        """Sync all deprecation sources"""
        logger.info("Starting deprecation sync...")
        try:
            all_rules = []
            
            # Fetch from multiple sources
            all_rules.extend(self._fetch_github_releases())
            all_rules.extend(self._fetch_breaking_changes_doc())
            all_rules.extend(self._fetch_platform_changes())
            all_rules.extend(self._parse_common_patterns())
            
            self.deprecations = {
                'rules': all_rules,
                'last_updated': datetime.now().isoformat(),
                'count': len(all_rules),
                'sources': list(set([r.get('source', 'unknown') for r in all_rules]))
            }
            
            self._save_cache()
            
            # Save sync timestamp
            with open(LAST_SYNC_FILE, 'w') as f:
                json.dump({'last_sync': datetime.now().isoformat()}, f)
            
            logger.info(f"Sync completed. Found {len(all_rules)} deprecation rules")
            return True
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return False
    
    def get_rules(self):
        """Get current deprecation rules"""
        return self.deprecations

# Initialize manager
manager = DeprecationManager()

# Schedule background sync
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=manager.sync,
    trigger='interval',
    minutes=SYNC_INTERVAL,
    id='deprecation_sync',
    name='Sync deprecation data'
)

# API Endpoints
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend HTML"""
    return send_from_directory('/app', 'index.html')

@app.route('/api/deprecations', methods=['GET'])
def get_deprecations():
    """Get current deprecation rules"""
    return jsonify(manager.get_rules()), 200

@app.route('/api/sync', methods=['POST'])
def manual_sync():
    """Manually trigger deprecation sync"""
    success = manager.sync()
    return jsonify({
        'success': success,
        'message': 'Sync completed successfully' if success else 'Sync failed',
        'deprecations': manager.get_rules()
    }), 200 if success else 500

@app.route('/api/validate', methods=['POST'])
def validate_yaml():
    """Validate YAML against deprecation rules"""
    data = request.json
    yaml_content = data.get('yaml', '')
    
    if not yaml_content:
        return jsonify({'error': 'No YAML content provided'}), 400
    
    issues = []
    
    try:
        yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        issues.append({
            'type': 'error',
            'message': f'YAML Syntax Error: {str(e)}',
            'severity': 'critical'
        })
    
    # Check against deprecation rules
    rules = manager.get_rules().get('rules', [])
    for rule in rules:
        old_pattern = rule.get('old_pattern', '')
        if old_pattern and old_pattern in yaml_content:
            issues.append({
                'type': 'deprecated',
                'pattern': old_pattern,
                'suggestion': rule.get('new_pattern', 'See documentation'),
                'description': rule.get('description', ''),
                'source': rule.get('source', 'unknown')
            })
    
    return jsonify({
        'valid': len([i for i in issues if i['type'] == 'error']) == 0,
        'issues': issues,
        'issue_count': len(issues)
    }), 200

@app.route('/api/status', methods=['GET'])
def status():
    """Get addon status and information"""
    last_sync = None
    if LAST_SYNC_FILE.exists():
        with open(LAST_SYNC_FILE, 'r') as f:
            last_sync = json.load(f).get('last_sync')
    
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'sync_interval_minutes': SYNC_INTERVAL,
        'last_sync': last_sync,
        'deprecations_count': manager.get_rules().get('count', 0),
        'sources': manager.get_rules().get('sources', []),
        'cache_max_age_seconds': MAX_CACHE_AGE
    }), 200

if __name__ == '__main__':
    # Start scheduler
    scheduler.start()
    logger.info(f"Starting HA YAML Corrector on port 8080")
    logger.info(f"Sync interval: {SYNC_INTERVAL} minutes")
    
    # Initial sync
    manager.sync()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)
