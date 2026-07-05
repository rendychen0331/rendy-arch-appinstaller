import subprocess
import re
import urllib.request
import urllib.parse
import json

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
    except Exception as e:
        print(f"Official API search failed: {e}")
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
    except Exception as e:
        print(f"AUR API search failed: {e}")
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
    except Exception as e:
        print(f"Error running local yay: {e}")
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
    except Exception as e:
        print(f"Error running flatpak: {e}")
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
    except Exception as e:
        print(f"Error searching npm packages: {e}")
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
            arch_pkgs = []
            if include_pacman:
                arch_pkgs = search_official_packages_api(q_item, installed_dict)
            aur_pkgs = []
            if include_aur and arch_pkgs is not None:
                aur_pkgs = search_aur_packages_api(q_item, installed_dict)
                
            if (include_pacman and arch_pkgs is None) or (include_aur and aur_pkgs is None):
                # Fallback to local
                arch_pkgs = search_arch_packages_local(q_item, installed_dict) if include_pacman else []
                aur_pkgs = []
                
            combined_arch.extend((arch_pkgs or []) + (aur_pkgs or []))
        
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
        
        # Smart VS Code & Chrome alias matching
        is_vscode_query = q in ('vscode', 'vs-code', 'vsc')
        is_chrome_query = q in ('google chrome', 'google-chrome', 'chrome')
        norm_name = name.replace('-', ' ').replace('_', ' ')
        norm_id = app_id.replace('-', ' ').replace('_', ' ')
        
        # 1. Exact name match
        if name == q or (is_vscode_query and (name == 'visual-studio-code' or norm_name == 'visual studio code')) or (is_chrome_query and name == 'google-chrome'):
            return 0
            
        # 2. Exact ID match
        if app_id == q or (is_chrome_query and (app_id == 'com.google.chrome' or norm_id == 'com google chrome')):
            return 1
            
        # 3. Word-boundary match in package name
        name_words = re.split(r'[\-_\.\s]+', name)
        if q in name_words or (is_vscode_query and (name == 'code' or 'visual studio code' in norm_name)) or (is_chrome_query and name == 'google-chrome-beta'):
            return 2
            
        # 4. Package name starts with query
        if name.startswith(q):
            return 3
            
        # 5. Word-boundary match in app ID
        id_words = re.split(r'[\-_\.\s]+', app_id)
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
        src = pkg['source']
        if src == 'Pacman':
            return 0
        elif src == 'AUR':
            return 1
        elif src == 'Flatpak':
            return 2
        else:
            return 3

    combined.sort(key=lambda x: (
        0 if (x['installed'] and match_score(x) < 8) else 1,
        match_score(x),
        -x.get('popularity', 0.0),
        source_priority(x),
        len(x['name'])
    ))
    
    return combined[:80]

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
