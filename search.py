import subprocess
import re
import urllib.request
import urllib.parse
import json
import logging
import os

logger = logging.getLogger(__name__)

# Load app aliases if available
ALIASES_MAP = {} # maps alias -> list of (package_name, source)
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    aliases_path = os.path.join(base_dir, "app-aliases.json")
    if os.path.exists(aliases_path):
        with open(aliases_path, 'r', encoding='utf-8') as f:
            aliases_data = json.load(f)
            for app in aliases_data.get("apps", []):
                pkg_name = app.get("package")
                src = app.get("source") # official | aur | flatpak
                aliases = app.get("aliases", [])
                for alias in aliases:
                    alias_clean = alias.strip().lower()
                    if alias_clean:
                        if alias_clean not in ALIASES_MAP:
                            ALIASES_MAP[alias_clean] = []
                        ALIASES_MAP[alias_clean].append((pkg_name, src))
except Exception:
    logger.exception("Error loading app-aliases.json")


def get_installed_pacman_packages_dict():
    try:
        res = subprocess.run(
            ['pacman', '-Q'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if res.returncode == 0:
            installed = {}
            for line in res.stdout.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    installed[parts[0]] = parts[1]
            return installed
    except Exception:
        pass
    return {}

def get_installed_flatpaks_dict():
    try:
        res = subprocess.run(
            ['flatpak', 'list', '--columns=application,version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if res.returncode == 0:
            installed = {}
            for line in res.stdout.split('\n'):
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    installed[parts[0].strip()] = parts[1].strip()
            return installed
    except Exception:
        pass
    return {}

def is_flatpak_installed(app_id):
    try:
        res = subprocess.run(
            ['flatpak', 'info', app_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return res.returncode == 0
    except Exception:
        return False

# --- WEB API SEARCH IMPLEMENTATION ---

def search_official_packages_api(query, installed_dict):
    try:
        url = f"https://archlinux.org/packages/search/json/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ArchAppInstaller)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            results = data.get('results', [])
            
            packages = []
            for item in results:
                name = item.get('pkgname', '') or ''
                version = f"{item.get('pkgver', '') or ''}-{item.get('pkgrel', '') or ''}"
                desc = item.get('pkgdesc', '') or ''
                repo = item.get('repo', '') or ''
                
                is_installed = name in installed_dict
                inst_ver = installed_dict.get(name) if is_installed else None
                has_update = is_installed and inst_ver and inst_ver != version
                
                packages.append({
                    'name': name,
                    'app_id': name,
                    'repo': repo,
                    'version': version,
                    'description': desc,
                    'source': 'Pacman',
                    'installed': is_installed,
                    'installed_version': inst_ver,
                    'has_update': has_update,
                    'raw_repo': repo,
                    'popularity': 1000.0
                })
            return packages
    except Exception:
        logger.warning("Official API search failed for %r", query, exc_info=True)
        return None

def search_aur_packages_api(query, installed_dict):
    try:
        url = f"https://aur.archlinux.org/rpc/?v=5&type=search&arg={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ArchAppInstaller)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            results = data.get('results', [])
            
            packages = []
            for item in results:
                name = item.get('Name', '') or ''
                version = item.get('Version', '') or ''
                desc = item.get('Description', '') or ''
                
                is_installed = name in installed_dict
                inst_ver = installed_dict.get(name) if is_installed else None
                has_update = is_installed and inst_ver and inst_ver != version
                
                packages.append({
                    'name': name,
                    'app_id': name,
                    'repo': 'aur',
                    'version': version,
                    'description': desc,
                    'source': 'AUR',
                    'installed': is_installed,
                    'installed_version': inst_ver,
                    'has_update': has_update,
                    'raw_repo': 'aur',
                    'popularity': float(item.get('Popularity', 0.0))
                })
            return packages
    except Exception:
        logger.warning("AUR API search failed for %r", query, exc_info=True)
        return None

# --- LOCAL COMMAND FALLBACK IMPLEMENTATION ---

def search_arch_packages_local(query, installed_dict):
    try:
        result = subprocess.run(
            ['yay', '-Ss', query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        lines = result.stdout.split('\n')
    except Exception:
        logger.exception("Error running local yay")
        return []

    packages = []
    current_pkg = None
    
    # Match: repo/name version [groups/installed]
    header_pattern = re.compile(r'^([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-\+]+)\s+([^\s]+)(.*)$')
    
    for line in lines:
        if not line.strip():
            continue
        
        match = header_pattern.match(line)
        if match:
            if current_pkg:
                packages.append(current_pkg)
            
            repo = match.group(1)
            name = match.group(2)
            version = match.group(3)
            extra = match.group(4).strip()
            
            # Extract popularity from local extra text e.g. (+1690 31.17)
            pop_match = re.search(r'\(\+[^ ]+\s+([\d\.]+)\)', extra)
            popularity = float(pop_match.group(1)) if pop_match else 0.0
            if repo.lower() != 'aur':
                popularity = 1000.0
                
            is_installed = name in installed_dict
            inst_ver = installed_dict.get(name) if is_installed else None
            has_update = is_installed and inst_ver and inst_ver != version
            
            current_pkg = {
                'name': name,
                'app_id': name,
                'repo': repo,
                'version': version,
                'description': '',
                'source': 'AUR' if repo.lower() == 'aur' else 'Pacman',
                'installed': is_installed,
                'installed_version': inst_ver,
                'has_update': has_update,
                'raw_repo': repo,
                'popularity': popularity
            }
        else:
            if current_pkg:
                desc = line.strip()
                if current_pkg['description']:
                    current_pkg['description'] += ' ' + desc
                else:
                    current_pkg['description'] = desc
                    
    if current_pkg:
        packages.append(current_pkg)
        
    return packages

# --- FLATPAK SEARCH ---

def search_flatpak_packages(query):
    if not query.strip():
        return []
    try:
        result = subprocess.run(
            ['flatpak', 'search', query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.split('\n')
    except Exception:
        logger.exception("Error running flatpak")
        return []

    installed_dict = get_installed_flatpaks_dict()
    packages = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 4:
            name = parts[0].strip()
            desc = parts[1].strip()
            app_id = parts[2].strip()
            version = parts[3].strip()
            
            is_installed = app_id in installed_dict
            inst_ver = installed_dict.get(app_id) if is_installed else None
            has_update = is_installed and inst_ver and inst_ver != version
            
            packages.append({
                'name': name,
                'app_id': app_id,
                'repo': 'flathub',
                'version': version,
                'description': desc,
                'source': 'Flatpak',
                'installed': is_installed,
                'installed_version': inst_ver,
                'has_update': has_update,
                'raw_repo': 'flathub',
                'popularity': 100.0
            })
    return packages

# --- NPM SEARCH HELPERS ---

def get_installed_npm_packages_dict():
    installed = {}
    try:
        res = subprocess.run(
            ['npm', 'list', '-g', '--depth=0', '--json'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if res.returncode == 0:
            data = json.loads(res.stdout)
            dependencies = data.get('dependencies', {})
            for name, info in dependencies.items():
                installed[name] = info.get('version', '')
    except Exception:
        pass
    return installed

def search_npm_packages(query, installed_npm_dict):
    if not query.strip():
        return []
    try:
        url = f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(query)}&size=30"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ArchAppInstaller)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            results = []
            for item in data.get('objects', []):
                pkg = item.get('package', {})
                name = pkg.get('name')
                if not name:
                    continue
                version = pkg.get('version', '')
                desc = pkg.get('description', '')
                
                # Check if installed
                installed_ver = installed_npm_dict.get(name)
                is_installed = installed_ver is not None
                
                # Check for update
                has_update = False
                if is_installed and version and installed_ver != version:
                    has_update = True
                
                results.append({
                    'name': name,
                    'app_id': name,
                    'version': version,
                    'source': 'npm',
                    'repo': 'npm Registry',
                    'description': desc,
                    'installed': is_installed,
                    'installed_version': installed_ver or '',
                    'has_update': has_update,
                    'popularity': item.get('score', {}).get('detail', {}).get('popularity', 0.0)
                })
            return results
    except Exception:
        logger.warning("Error searching npm packages for %r", query, exc_info=True)
    return []

# --- UNIFIED SEARCH PIPELINE ---

def search_all(query, include_pacman=True, include_aur=True, include_flatpak=True, include_npm=True):
    if not query.strip():
        return []
    
    # 1. Fetch local installed package list with versions once
    installed_dict = get_installed_pacman_packages_dict() if (include_pacman or include_aur) else {}
    installed_npm_dict = get_installed_npm_packages_dict() if include_npm else {}
    
    # Generate query variations to handle spaces (e.g., "google chrome" -> ["google chrome", "google-chrome"])
    queries = [query]
    normalized = query.replace(' ', '-')
    if normalized != query:
        queries.append(normalized)
        
    combined_arch = []
    
    if include_pacman or include_aur:
        for q_item in queries:
            arch_pkgs = search_official_packages_api(q_item, installed_dict) if include_pacman else []
            aur_pkgs = search_aur_packages_api(q_item, installed_dict) if include_aur else []

            # A disabled source yields [], so None here means only "that API call failed".
            if arch_pkgs is None or aur_pkgs is None:
                # `yay -Ss` indexes the official repos and the AUR together, so one
                # local run can back-fill whichever leg lost its API.
                local_pkgs = search_arch_packages_local(q_item, installed_dict)
                if arch_pkgs is None:
                    arch_pkgs = [p for p in local_pkgs if p['source'] == 'Pacman']
                if aur_pkgs is None:
                    aur_pkgs = [p for p in local_pkgs if p['source'] == 'AUR']

            combined_arch.extend(arch_pkgs + aur_pkgs)
        
    # De-duplicate by name and source
    seen = set()
    unique_arch = []
    for pkg in combined_arch:
        key = (pkg['name'], pkg['source'])
        if key not in seen:
            seen.add(key)
            unique_arch.append(pkg)

    # 5. Fetch Flatpaks
    flatpak_pkgs = []
    if include_flatpak:
        flatpak_pkgs = search_flatpak_packages(query)
        
    # 6. Fetch npm packages
    npm_pkgs = []
    if include_npm:
        npm_pkgs = search_npm_packages(query, installed_npm_dict)
    
    combined = unique_arch + flatpak_pkgs + npm_pkgs
    
    # 7. Sort by match score and installed status to keep GUI rendering smooth
    q = query.lower()
    
    def match_score(pkg):
        name = (pkg.get('name') or '').lower()
        app_id = (pkg.get('app_id') or '').lower()
        desc = (pkg.get('description') or '').lower()
        
        # Check app-aliases.json
        src_map = {
            'Pacman': 'official',
            'AUR': 'aur',
            'Flatpak': 'flatpak',
            'npm': 'npm'
        }
        pkg_src = src_map.get(pkg.get('source'), '').lower()
        query_clean = q.strip()
        matched_targets = ALIASES_MAP.get(query_clean, [])
        for target_pkg, target_src in matched_targets:
            if target_pkg == name:
                if target_src.lower() == pkg_src or (target_src.lower() == 'official-multilib' and pkg_src == 'official'):
                    return -1 # Curated alias matches get absolute highest priority!
        
        # 1. Exact name match
        if name == q:
            return 0
            
        # 2. Exact ID match
        if app_id == q:
            return 1
            
        # 3. Word-boundary match in package name
        name_words = re.split(r'[\-_\.\s/@]+', name)
        if q in name_words:
            return 2
            
        # 4. Package name starts with query
        if name.startswith(q):
            return 3
            
        # 5. Word-boundary match in app ID
        id_words = re.split(r'[\-_\.\s/@]+', app_id)
        if q in id_words:
            return 4
            
        # 6. Word-boundary match in description
        desc_words = re.split(r'[\-_\.\s\(\):]+', desc)
        if q in desc_words:
            return 5
            
        # 7. App ID starts with query
        if app_id.startswith(q):
            return 6
            
        # 8. Substring match in package name
        if q in name:
            return 7
            
        # 9. Substring match in app ID
        if q in app_id:
            return 8
            
        # 10. Substring match in description
        if q in desc:
            return 9
            
        # 11. Description match only
        return 10

    def source_priority(pkg):
        # Pacman > AUR > npm > Flatpak: prefer the system package manager, then the
        # community repo, then language-specific and sandboxed sources.
        return {'Pacman': 0, 'AUR': 1, 'npm': 2, 'Flatpak': 3}.get(pkg['source'], 4)

    # Score once per package: match_score re-splits names with regex, and sort()
    # would otherwise call it on every comparison.
    scored = [(match_score(pkg), pkg) for pkg in combined]
    scored.sort(key=lambda item: (
        0 if (item[1]['installed'] and item[0] < 8) else 1,
        item[0],
        source_priority(item[1]),
        -item[1].get('popularity', 0.0),
        len(item[1]['name'])
    ))

    return [pkg for _, pkg in scored[:80]]

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "visual-studio-code-bin"
    print(f"Searching for '{q}'...")
    results = search_all(q)
    print(f"Found {len(results)} results:")
    for r in results[:10]:
        status = "[Installed]" if r['installed'] else ""
        if r['installed'] and r.get('has_update'):
            status = "[Installed, Update Available]"
        print(f"- [{r['source']}] {r['name']} ({r['version']}) {status}\n  {r['description']}\n")
