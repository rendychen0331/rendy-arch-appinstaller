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

# --- UNIFIED SEARCH PIPELINE ---

def search_all(query):
    if not query.strip():
        return []
    
    # 1. Fetch local installed package list with versions once
    installed_dict = get_installed_pacman_packages_dict()
    
    # 2. Try official JSON API first
    arch_pkgs = search_official_packages_api(query, installed_dict)
    aur_pkgs = None
    
    # 3. If official API succeeded, fetch AUR API
    if arch_pkgs is not None:
        aur_pkgs = search_aur_packages_api(query, installed_dict)
        
    # 4. Fallback to local 'yay' execution if any web API failed
    if arch_pkgs is None or aur_pkgs is None:
        print("[*] Web API failed or offline. Falling back to local yay command...")
        combined_arch = search_arch_packages_local(query, installed_dict)
    else:
        combined_arch = arch_pkgs + aur_pkgs

    # 5. Fetch Flatpaks (local cache search is extremely fast)
    flatpak_pkgs = search_flatpak_packages(query)
    
    combined = combined_arch + flatpak_pkgs
    
    # 6. Sort by match score and installed status to keep GUI rendering smooth
    q = query.lower()
    
    def match_score(pkg):
        name = (pkg.get('name') or '').lower()
        app_id = (pkg.get('app_id') or '').lower()
        desc = (pkg.get('description') or '').lower()
        
        # Smart VS Code alias matching
        is_vscode_query = q in ('vscode', 'vs-code', 'vsc')
        norm_name = name.replace('-', ' ').replace('_', ' ')
        
        # 1. Exact name match
        if name == q or (is_vscode_query and (name == 'visual-studio-code' or norm_name == 'visual studio code')):
            return 0
            
        # 2. Exact ID match
        if app_id == q:
            return 1
            
        # 3. Word-boundary match in package name
        name_words = re.split(r'[\-_\.\s]+', name)
        if q in name_words or (is_vscode_query and (name == 'code' or 'visual studio code' in norm_name)):
            return 2
            
        # 4. Package name starts with query
        if name.startswith(q):
            return 3
            
        # 5. Word-boundary match in app ID
        id_words = re.split(r'[\-_\.\s]+', app_id)
        if q in id_words:
            return 4
            
        # 6. Word-boundary match in description (e.g. 'vscode' in description of 'visual-studio-code-bin')
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

    # Sort: 
    # 1. Prioritize installed packages if they match the query in name, ID, or description words (score < 8)
    # 2. Match score (lower is more relevant)
    # 3. Popularity (descending)
    # 4. Source priority: Pacman (0) ➔ AUR (1) ➔ Flatpak (2)
    # 5. Name length (shorter first)
    def source_priority(pkg):
        src = pkg['source']
        if src == 'Pacman':
            return 0
        elif src == 'AUR':
            return 1
        else:
            return 2

    combined.sort(key=lambda x: (
        0 if (x['installed'] and match_score(x) < 8) else 1,
        match_score(x),
        -x.get('popularity', 0.0),
        source_priority(x),
        len(x['name'])
    ))
    
    # Limit to top 80 results for instant rendering
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
