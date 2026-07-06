import sys
import os
import threading
import subprocess
import re
import json
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GLib, Gio, Adw

# Import search functions
from search import search_all, is_flatpak_installed

# --- INTERNATIONALIZATION (i18n) CONFIGURATION ---
CONFIG_DIR = os.path.expanduser("~/.config/rendy-arch-appinstaller")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(config):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception:
        pass

TRANSLATIONS = {
    'zh_TW': {
        'window_title': 'Linux 軟體商店',
        'window_subtitle': '探索、安裝、管理應用軟體',
        'app_title': '應用商店',
        'tab_installed': '📦 已安裝管理',
        'tab_search': '🔍 軟體搜尋',
        'tab_updates': '⚙️ 可更新項目',
        'sub_installed': '管理您已安裝的應用程式',
        'sub_search': '搜尋 Pacman、AUR 與 Flatpak 軟體包',
        'sub_updates': '系統安全更新與軟體升級',
        'search_title': '軟體搜尋',
        'search_placeholder': '輸入關鍵字進行搜尋，例如：code, gimp, chrome...',
        'btn_search': '🔍 搜尋',
        'btn_auto_install': '⚡ 一鍵自動安裝',
        'filter_pacman': '官方倉庫 (Pacman)',
        'filter_aur': '使用者倉庫 (AUR)',
        'filter_flatpak': '沙盒套件 (Flatpak)',
        'filter_npm': 'Node 套件 (npm)',
        'search_intro': '輸入關鍵字，探索您的系統應用',
        'search_loading': '正在搜尋 \'{query}\'，請稍候...',
        'installed_title': '已安裝的軟體',
        'btn_refresh': '🔄 重新整理',
        'no_installed_packages': '目前無已安裝的套件。',
        'desc_aur': '系統社群軟體包 (AUR Explicit)',
        'desc_pacman': '系統官方軟體包 (Pacman Explicit)',
        'desc_flatpak': 'Flatpak 沙盒應用程式 ({app_id})',
        'label_has_update': '▲ 有更新 (本機: {version})',
        'label_installed': '✓ 已安裝',
        'no_description': '無詳細描述。',
        'pkg_details': '版本: {version} | 庫區: {repo}',
        'btn_update_pkg': '更新',
        'btn_reinstall_pkg': '重新安裝',
        'btn_install_pkg': '安裝',
        'updates_title': '系統更新與升級',
        'btn_update_all': '⚡ 全部更新',
        'btn_check_updates': '🔄 檢查更新',
        'system_up_to_date': '所有軟體皆為最新，無須更新！',
        'update_detail': '待更新: {old} ➔ {new}',
        'btn_upgrade_single': '升級',
        'install_title_running': '正在執行操作...',
        'install_status_preparing': '正在準備...',
        'btn_cancel': '取消',
        'btn_back': '返回首頁',
        'status_installing': '正在安裝 \'{pkg_name}\'...',
        'status_uninstalling': '正在卸載 \'{pkg_name}\'...',
        'status_upgrading': '正在升級 \'{pkg_name}\'...',
        'status_sys_upgrade': '正在執行全系統升級...',
        'status_searching_match': '搜尋匹配的套件中...',
        'status_preparing': '準備中...',
        'status_preparing_uninstall': '準備卸載中...',
        'status_preparing_upgrade': '準備升級中...',
        'status_sys_upgrade_running': '全系統升級中...',
        'status_preparing_local': '準備安裝本地檔...',
        'status_cancelling': '正在取消中...',
        'msg_install_success': '成功安裝 \'{name}\'。',
        'msg_install_failed': '安裝 \'{name}\' 失敗。',
        'msg_pacman_success': '成功透過 Pacman 安裝 \'{name}\'。',
        'msg_aur_success': '成功透過 AUR 安裝 \'{name}\'。',
        'msg_flatpak_success': '成功透過 Flatpak 安裝 \'{name}\'。',
        'msg_uninstall_success': '成功卸載 \'{name}\'。',
        'msg_uninstall_failed': '卸載 \'{name}\' 失敗。',
        'msg_auto_install_failed': '自動安裝失敗：在 Pacman, AUR 及 Flatpak 中皆找不到或無法安裝 \'{name}\'。',
        'terminal_pre_auth': '[*] 正在驗證管理員授權以利後續自動安裝...\n',
        'terminal_pre_auth_success': '[+] 授權成功，開始編譯與安裝。\n',
        'terminal_pre_auth_failed': '[-] 管理員授權失敗，取消安裝。\n',
    },
    'zh_CN': {
        'window_title': 'Linux 软件商店',
        'window_subtitle': '探索、安装、管理应用软件',
        'app_title': '应用商店',
        'tab_installed': '📦 已安装管理',
        'tab_search': '🔍 软件搜寻',
        'tab_updates': '⚙️ 可更新项目',
        'sub_installed': '管理您已安装的应用程序',
        'sub_search': '搜寻 Pacman、AUR 与 Flatpak 软件包',
        'sub_updates': '系统安全更新与软件升级',
        'search_title': '软件搜寻',
        'search_placeholder': '输入关键字进行搜寻，例如：code, gimp, chrome...',
        'btn_search': '🔍 搜寻',
        'btn_auto_install': '⚡ 一键自动安装',
        'filter_pacman': '官方仓库 (Pacman)',
        'filter_aur': '使用者仓库 (AUR)',
        'filter_flatpak': '沙盒套件 (Flatpak)',
        'filter_npm': 'Node 套件 (npm)',
        'search_intro': '输入关键字，探索您的系统应用',
        'search_loading': '正在搜寻 \'{query}\'，请稍候...',
        'installed_title': '已安装的软件',
        'btn_refresh': '🔄 重新整理',
        'no_installed_packages': '目前无已安装的套件。',
        'desc_aur': '系统社群软件包 (AUR Explicit)',
        'desc_pacman': '系统官方软件包 (Pacman Explicit)',
        'desc_flatpak': 'Flatpak 沙盒应用程序 ({app_id})',
        'label_has_update': '▲ 有更新 (本机: {version})',
        'label_installed': '✓ 已安装',
        'no_description': '无详细描述。',
        'pkg_details': '版本: {version} | 库区: {repo}',
        'btn_update_pkg': '更新',
        'btn_reinstall_pkg': '重新安装',
        'btn_install_pkg': '安装',
        'updates_title': '系统更新与升级',
        'btn_update_all': '⚡ 全部更新',
        'btn_check_updates': '🔄 检查更新',
        'system_up_to_date': '所有软件皆为最新，无须更新！',
        'update_detail': '待更新: {old} ➔ {new}',
        'btn_upgrade_single': '升级',
        'install_title_running': '正在执行操作...',
        'install_status_preparing': '正在准备...',
        'btn_cancel': '取消',
        'btn_back': '返回首页',
        'status_installing': '正在安装 \'{pkg_name}\'...',
        'status_uninstalling': '正在卸载 \'{pkg_name}\'...',
        'status_upgrading': '正在升级 \'{pkg_name}\'...',
        'status_sys_upgrade': '正在执行全系统升级...',
        'status_searching_match': '搜寻匹配的套件中...',
        'status_preparing': '准备中...',
        'status_preparing_uninstall': '准备卸载中...',
        'status_preparing_upgrade': '准备升级中...',
        'status_sys_upgrade_running': '全系统升级中...',
        'status_preparing_local': '准备安装本地档...',
        'status_cancelling': '正在取消中...',
        'msg_install_success': '成功安装 \'{name}\'。',
        'msg_install_failed': '安装 \'{name}\' 失败。',
        'msg_pacman_success': '成功透过 Pacman 安装 \'{name}\'。',
        'msg_aur_success': '成功透過 AUR 安装 \'{name}\'。',
        'msg_flatpak_success': '成功透过 Flatpak 安装 \'{name}\'。',
        'msg_uninstall_success': '成功卸载 \'{name}\'。',
        'msg_uninstall_failed': '卸载 \'{name}\' 失败。',
        'msg_auto_install_failed': '自动安装失败：在 Pacman, AUR 及 Flatpak 中皆找不到或无法安装 \'{name}\'。',
        'terminal_pre_auth': '[*] 正在验证管理员授权以利后续自动安装...\n',
        'terminal_pre_auth_success': '[+] 授权成功，开始编译与安装。\n',
        'terminal_pre_auth_failed': '[-] 管理员授权失败，取消安装。\n',
    },
    'en': {
        'window_title': 'Linux App Store',
        'window_subtitle': 'Discover, install, and manage software',
        'app_title': 'App Store',
        'tab_installed': '📦 Installed',
        'tab_search': '🔍 Search',
        'tab_updates': '⚙️ Updates',
        'sub_installed': 'Manage your installed applications',
        'sub_search': 'Search Pacman, AUR, and Flatpak packages',
        'sub_updates': 'System safety updates and package upgrades',
        'search_title': 'Software Search',
        'search_placeholder': 'Enter keywords to search, e.g. code, gimp, chrome...',
        'btn_search': '🔍 Search',
        'btn_auto_install': '⚡ One-Click Install',
        'filter_pacman': 'Official Repo (Pacman)',
        'filter_aur': 'User Repo (AUR)',
        'filter_flatpak': 'Sandbox (Flatpak)',
        'filter_npm': 'Node Packages (npm)',
        'search_intro': 'Enter keywords to discover system applications',
        'search_loading': 'Searching for \'{query}\', please wait...',
        'installed_title': 'Installed Applications',
        'btn_refresh': '🔄 Refresh',
        'no_installed_packages': 'No packages installed currently.',
        'desc_aur': 'System Community Package (AUR Explicit)',
        'desc_pacman': 'System Official Package (Pacman Explicit)',
        'desc_flatpak': 'Flatpak Sandbox Application ({app_id})',
        'label_has_update': '▲ Update available (Local: {version})',
        'label_installed': '✓ Installed',
        'no_description': 'No description available.',
        'pkg_details': 'Version: {version} | Repo: {repo}',
        'btn_update_pkg': 'Update',
        'btn_reinstall_pkg': 'Reinstall',
        'btn_install_pkg': 'Install',
        'updates_title': 'System Updates',
        'btn_update_all': '⚡ Update All',
        'btn_check_updates': '🔄 Check Updates',
        'system_up_to_date': 'All packages are up to date!',
        'update_detail': 'Update: {old} ➔ {new}',
        'btn_upgrade_single': 'Upgrade',
        'install_title_running': 'Executing operation...',
        'install_status_preparing': 'Preparing...',
        'btn_cancel': 'Cancel',
        'btn_back': 'Back to Home',
        'status_installing': 'Installing \'{pkg_name}\'...',
        'status_uninstalling': 'Uninstalling \'{pkg_name}\'...',
        'status_upgrading': 'Upgrading \'{pkg_name}\'...',
        'status_sys_upgrade': 'Running full system upgrade...',
        'status_searching_match': 'Searching for matching packages...',
        'status_preparing': 'Preparing...',
        'status_preparing_uninstall': 'Preparing to uninstall...',
        'status_preparing_upgrade': 'Preparing to upgrade...',
        'status_sys_upgrade_running': 'System upgrade in progress...',
        'status_preparing_local': 'Preparing local package installation...',
        'status_cancelling': 'Cancelling...',
        'msg_install_success': 'Successfully installed \'{name}\'.',
        'msg_install_failed': 'Failed to install \'{name}\'.',
        'msg_pacman_success': 'Successfully installed \'{name}\' via Pacman.',
        'msg_aur_success': 'Successfully installed \'{name}\' via AUR.',
        'msg_flatpak_success': 'Successfully installed \'{name}\' via Flatpak.',
        'msg_uninstall_success': 'Successfully uninstalled \'{name}\'.',
        'msg_uninstall_failed': 'Failed to uninstall \'{name}\'.',
        'msg_auto_install_failed': 'Auto-install failed: \'{name}\' not found or could not be installed.',
        'terminal_pre_auth': '[*] Authenticating administrator privilege for automatic installation...\n',
        'terminal_pre_auth_success': '[+] Authentication succeeded. Starting compilation and installation.\n',
        'terminal_pre_auth_failed': '[-] Authentication failed. Aborting installation.\n',
    }
}

class AppInstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        # Load user configuration
        self.config = load_config()
        
        # Auto-detect language
        default_lang = 'zh_TW'
        lang_env = os.environ.get('LANG', '')
        if 'zh_CN' in lang_env:
            default_lang = 'zh_CN'
        elif 'en' in lang_env:
            default_lang = 'en'
            
        self.current_lang = self.config.get('language', default_lang)
        self.should_cancel = False
        
        self.set_title(self.tr('window_title'))
        self.set_default_size(960, 690)
        
        # Build UI
        self.build_ui()

    def setup_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            /* Sidebar navigation styling */
            .sidebar-panel {
                background-color: #1e1e1e;
                border-right: 1px solid #2d2d2d;
                padding: 10px;
            }
            .sidebar-item {
                border-radius: 8px;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 0.95rem;
                margin-bottom: 3px;
                color: #e0e0e0;
                transition: background-color 0.2s;
            }
            .sidebar-item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            .sidebar-item.selected {
                background-color: #3584e4;
                color: white;
            }
            .sidebar-badge {
                background-color: #e66100;
                color: white;
                font-size: 0.75rem;
                padding: 1px 6px;
                border-radius: 10px;
                font-weight: bold;
                margin-left: 6px;
            }
            
            /* Discover page styling */
            .featured-banner {
                background: linear-gradient(135deg, #350068 0%, #1a0f91 100%);
                padding: 28px;
                border-radius: 12px;
                color: white;
                margin-bottom: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            .banner-title {
                font-size: 1.8rem;
                font-weight: 800;
            }
            .banner-subtitle {
                font-size: 0.95rem;
                opacity: 0.8;
                margin-top: 6px;
            }
            
            /* Section titles */
            .section-title {
                font-size: 1.2rem;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 12px;
                color: white;
            }
            
            /* Category button styling */
            .category-btn {
                background-color: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 0.9rem;
                color: #e0e0e0;
                transition: background-color 0.15s, border-color 0.15s;
            }
            .category-btn:hover {
                background-color: #3d3d3d;
                border-color: #5d5d5d;
            }
            
            /* App card styling */
            .app-card {
                background-color: #252525;
                border: 1px solid #353535;
                border-radius: 12px;
                padding: 16px;
                transition: transform 0.2s, background-color 0.2s, box-shadow 0.2s;
            }
            .app-card:hover {
                transform: translateY(-4px);
                background-color: #2e2e2e;
                border-color: #484848;
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
            }
            .app-card-icon {
                font-size: 2.2rem;
                margin-bottom: 8px;
            }
            .app-card-title {
                font-weight: bold;
                font-size: 0.95rem;
                color: white;
            }
            .app-card-desc {
                font-size: 0.78rem;
                color: #a8a8a8;
                line-height: 1.35;
                margin-top: 4px;
            }

            /* Badge classes */
            .badge-label {
                font-size: 0.75rem;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 12px;
            }
            .badge-pacman {
                background-color: #3584e4;
                color: white;
            }
            .badge-aur {
                background-color: #e66100;
                color: white;
            }
            .badge-flatpak {
                background-color: #9141ac;
                color: white;
            }
            .badge-npm {
                background-color: #cb3837;
                color: white;
            }
            .success-label {
                color: #2ec27e;
                font-weight: bold;
                font-size: 0.85rem;
            }
            .warning-label {
                color: #e66100;
                font-weight: bold;
                font-size: 0.85rem;
            }
            .dim-label {
                opacity: 0.7;
                font-size: 0.9rem;
            }
            .small-label {
                opacity: 0.5;
                font-size: 0.75rem;
            }
            .terminal-scroll {
                border: 1px solid #303030;
                border-radius: 8px;
                background-color: #181818;
            }
            .terminal-view {
                font-family: 'JetBrains Mono', 'Fira Code', 'Monospace', monospace;
                font-size: 0.95rem;
                background-color: #181818;
                color: #d4d4d4;
            }
            .package-row {
                padding: 10px;
                border-bottom: 1px solid rgba(128, 128, 128, 0.15);
            }
            .package-row:hover {
                background-color: rgba(128, 128, 128, 0.08);
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def build_ui(self):
        # Setup styling
        self.setup_css()
        
        # Main Split container (Sidebar + Content Stack)
        main_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # 1. Left Sidebar Panel
        sidebar_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar_panel.add_css_class("sidebar-panel")
        sidebar_panel.set_size_request(210, -1)
        
        # Sidebar Header
        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sidebar_header.set_margin_top(16)
        sidebar_header.set_margin_bottom(16)
        sidebar_header.set_margin_start(12)
        
        app_logo = Gtk.Label()
        app_logo.set_markup("<span size='large'>🛍️</span>")
        sidebar_header.append(app_logo)
        
        self.app_title_label = Gtk.Label()
        self.app_title_label.set_markup("<span weight='bold' size='medium'>應用商店</span>")
        sidebar_header.append(self.app_title_label)
        sidebar_panel.append(sidebar_header)
        
        # Sidebar Menu ListBox
        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-selected", self.on_sidebar_row_selected)
        
        self.row_installed = self.create_sidebar_row("", "installed_page")
        self.row_search = self.create_sidebar_row("", "search_page")
        self.row_updates = self.create_sidebar_row("", "updates_page")
        
        # Add badge container to updates row
        self.updates_badge_label = Gtk.Label(label="")
        self.updates_badge_label.add_css_class("sidebar-badge")
        self.updates_badge_label.set_visible(False)
        self.row_updates.get_child().append(self.updates_badge_label)
        
        self.sidebar_list.append(self.row_installed)
        self.sidebar_list.append(self.row_search)
        self.sidebar_list.append(self.row_updates)
        sidebar_panel.append(self.sidebar_list)
        
        # Spacer to push language switcher to the bottom
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar_panel.append(spacer)
        
        # Language Switcher
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lang_box.set_margin_start(12)
        lang_box.set_margin_end(12)
        lang_box.set_margin_bottom(16)
        lang_box.set_halign(Gtk.Align.FILL)
        
        lang_icon = Gtk.Image.new_from_icon_name("preferences-desktop-locale")
        lang_box.append(lang_icon)
        
        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("zh_TW", "繁體中文")
        self.lang_combo.append("zh_CN", "简体中文")
        self.lang_combo.append("en", "English")
        self.lang_combo.set_active_id(self.current_lang)
        self.lang_combo.set_hexpand(True)
        self.lang_combo.connect("changed", self.on_language_changed)
        
        # Disable scroll wheel event on ComboBox to prevent accidental language switches
        scroll_controller = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        scroll_controller.connect("scroll", lambda controller, dx, dy: True)
        self.lang_combo.add_controller(scroll_controller)
        
        lang_box.append(self.lang_combo)
        
        sidebar_panel.append(lang_box)
        
        main_layout.append(sidebar_panel)
        
        # 2. Right Side Content Panel
        right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_container.set_hexpand(True)
        right_container.set_vexpand(True)
        
        # Window Header
        self.header = Adw.HeaderBar()
        self.title_widget = Adw.WindowTitle(title="", subtitle="")
        self.header.set_title_widget(self.title_widget)
        right_container.append(self.header)
        
        # Main content View Stack
        self.main_stack = Adw.ViewStack()
        right_container.append(self.main_stack)
        
        main_layout.append(right_container)
        self.set_content(main_layout)
        
        # Create all sub-pages
        self.create_search_page()
        self.create_installed_page()
        self.create_updates_page()
        self.create_install_page()
        
        self.main_stack.add_named(self.installed_page, "installed_page")
        self.main_stack.add_named(self.search_page, "search_page")
        self.main_stack.add_named(self.updates_page, "updates_page")
        self.main_stack.add_named(self.install_page, "install_page")
        
        # Apply language updates to all UI elements
        self.apply_language()
        
        # Default select Installed tab
        self.sidebar_list.select_row(self.row_installed)
        
        # Check updates silently on startup (after 2 seconds)
        GLib.timeout_add_seconds(2, self.check_updates_startup)

    def create_sidebar_row(self, text, page_name):
        row = Gtk.ListBoxRow()
        row.page_name = page_name
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        lbl = Gtk.Label(label=text)
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)
        
        row.set_child(box)
        row.add_css_class("sidebar-item")
        row.label_widget = lbl
        return row

    def on_sidebar_row_selected(self, listbox, row):
        if row is not None:
            for child in listbox:
                child.remove_css_class("selected")
            row.add_css_class("selected")
            
            # Switch views
            self.main_stack.set_visible_child_name(row.page_name)
            
            # Update Header Subtitle and Refresh Lists
            if row.page_name == "installed_page":
                self.title_widget.set_subtitle(self.tr('sub_installed'))
                self.refresh_installed_list()
            elif row.page_name == "search_page":
                self.title_widget.set_subtitle(self.tr('sub_search'))
            elif row.page_name == "updates_page":
                self.title_widget.set_subtitle(self.tr('sub_updates'))
                self.refresh_updates_list()

    def tr(self, key):
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS['zh_TW']).get(key, key)

    def on_language_changed(self, combo):
        selected_id = combo.get_active_id()
        if hasattr(self, 'main_stack') and selected_id and selected_id != self.current_lang:
            self.current_lang = selected_id
            self.config['language'] = selected_id
            save_config(self.config)
            self.apply_language()

    def apply_language(self):
        # 1. Window Title & Subtitle
        self.set_title(self.tr('window_title'))
        self.title_widget.set_title(self.tr('window_title'))
        
        # 2. Sidebar items
        self.app_title_label.set_markup(f"<span weight='bold' size='medium'>{self.tr('app_title')}</span>")
        self.row_installed.label_widget.set_text(self.tr('tab_installed'))
        self.row_search.label_widget.set_text(self.tr('tab_search'))
        self.row_updates.label_widget.set_text(self.tr('tab_updates'))
        
        # Update active subtitle
        selected_row = self.sidebar_list.get_selected_row()
        if selected_row == self.row_installed:
            self.title_widget.set_subtitle(self.tr('sub_installed'))
        elif selected_row == self.row_search:
            self.title_widget.set_subtitle(self.tr('sub_search'))
        elif selected_row == self.row_updates:
            self.title_widget.set_subtitle(self.tr('sub_updates'))
            
        # 3. Search Page
        self.search_title.set_markup(f"<span size='large' weight='bold'>{self.tr('search_title')}</span>")
        self.search_entry.set_placeholder_text(self.tr('search_placeholder'))
        self.btn_search.set_label(self.tr('btn_search'))
        self.btn_auto_install.set_label(self.tr('btn_auto_install'))
        self.filter_pacman.set_label(self.tr('filter_pacman'))
        self.filter_aur.set_label(self.tr('filter_aur'))
        self.filter_flatpak.set_label(self.tr('filter_flatpak'))
        self.filter_npm.set_label(self.tr('filter_npm'))
        if not self.results_scroll.get_visible():
            self.search_status_label.set_text(self.tr('search_intro'))
            
        # 4. Installed Page
        self.installed_title.set_markup(f"<span size='large' weight='bold'>{self.tr('installed_title')}</span>")
        self.btn_refresh_installed.set_label(self.tr('btn_refresh'))
        
        # 5. Updates Page
        self.updates_title.set_markup(f"<span size='large' weight='bold'>{self.tr('updates_title')}</span>")
        self.btn_update_all.set_label(self.tr('btn_update_all'))
        self.btn_check_updates.set_label(self.tr('btn_check_updates'))
        
        # 6. Install Page
        self.btn_cancel_install.set_label(self.tr('btn_cancel'))
        self.btn_back_to_search.set_label(self.tr('btn_back'))
        
        # Force reload loaded list views to translate dynamic rows
        if selected_row == self.row_installed:
            self.refresh_installed_list()
        elif selected_row == self.row_updates:
            self.refresh_updates_list()

    # --- 1. DISCOVER PAGE ---

    def create_discover_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        container.set_margin_top(20)
        container.set_margin_bottom(20)
        container.set_margin_start(24)
        container.set_margin_end(24)
        
        # Hero Banner Card
        banner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        banner.add_css_class("featured-banner")
        
        banner_title = Gtk.Label()
        banner_title.set_markup("<span size='x-large' weight='bold'>探索精彩應用</span>")
        banner_title.set_halign(Gtk.Align.START)
        banner_title.add_css_class("banner-title")
        banner.append(banner_title)
        
        banner_subtitle = Gtk.Label()
        banner_subtitle.set_markup("<span>快速搜尋、一鍵安裝 Arch Linux 軟體，支援 Pacman、AUR 與 Flatpak</span>")
        banner_subtitle.set_halign(Gtk.Align.START)
        banner_subtitle.add_css_class("banner-subtitle")
        banner.append(banner_subtitle)
        container.append(banner)
        
        # Category Filters Section
        cat_title = Gtk.Label(label="熱門分類")
        cat_title.set_halign(Gtk.Align.START)
        cat_title.add_css_class("section-title")
        container.append(cat_title)
        
        cat_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        categories = [
            ("🛠️ 開發工具", "code"),
            ("🌐 網路瀏覽", "browser"),
            ("💬 社交溝通", "chat"),
            ("🎨 影音創作", "design"),
            ("🎮 遊戲娛樂", "game"),
            ("⚙️ 系統工具", "system")
        ]
        for name, query in categories:
            btn = Gtk.Button(label=name)
            btn.add_css_class("category-btn")
            btn.connect("clicked", lambda b, q=query: self.go_to_search_with_query(q))
            cat_hbox.append(btn)
        container.append(cat_hbox)
        
        # Recommended Apps Grid Section
        apps_title = Gtk.Label(label="熱門軟體推薦")
        apps_title.set_halign(Gtk.Align.START)
        apps_title.add_css_class("section-title")
        container.append(apps_title)
        
        apps_flowbox = Gtk.FlowBox()
        apps_flowbox.set_valign(Gtk.Align.START)
        apps_flowbox.set_column_spacing(16)
        apps_flowbox.set_row_spacing(16)
        apps_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        
        featured_apps = [
            {"name": "Visual Studio Code", "pkg": "vscode", "desc": "微軟官方熱門代碼編輯器，支援多語言與調試", "icon": "🛠️"},
            {"name": "Google Chrome", "pkg": "google-chrome", "desc": "由 Google 開發的快速、安全且熱門的網頁瀏覽器", "icon": "🌐"},
            {"name": "Firefox Browser", "pkg": "firefox", "desc": "開源隱私保護瀏覽器，快節奏網頁體驗", "icon": "🦊"},
            {"name": "Discord", "pkg": "discord", "desc": "針對玩家與社群的語音與文字聊天通訊軟體", "icon": "💬"},
            {"name": "Spotify", "pkg": "spotify", "desc": "全球熱門的音樂串流平台，百萬音樂隨身聽", "icon": "🎵"},
            {"name": "GIMP Image Editor", "pkg": "gimp", "desc": "強大的開源圖像編輯與照片修飾設計軟體", "icon": "🎨"},
            {"name": "Steam Client", "pkg": "steam", "desc": "Valve 遊戲平台，暢玩數千款 Linux 遊戲", "icon": "🎮"},
            {"name": "VLC Media Player", "pkg": "vlc", "desc": "全能開源影音播放器，支援播放各種媒體格式", "icon": "🎬"},
        ]
        for app in featured_apps:
            card = self.create_app_card(app)
            apps_flowbox.append(card)
        container.append(apps_flowbox)
        
        scroll.set_child(container)
        self.discover_page = scroll

    def create_app_card(self, app):
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card_box.add_css_class("app-card")
        card_box.set_size_request(195, 195)
        
        icon_lbl = Gtk.Label(label=app['icon'])
        icon_lbl.set_halign(Gtk.Align.START)
        icon_lbl.add_css_class("app-card-icon")
        card_box.append(icon_lbl)
        
        title_lbl = Gtk.Label(label=app['name'])
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("app-card-title")
        card_box.append(title_lbl)
        
        desc_lbl = Gtk.Label(label=app['desc'])
        desc_lbl.set_wrap(True)
        desc_lbl.set_max_width_chars(19)
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.add_css_class("app-card-desc")
        card_box.append(desc_lbl)
        
        # Click controller to trigger search
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("released", lambda g, n, x, y, q=app['pkg']: self.go_to_search_with_query(q))
        card_box.add_controller(click_gesture)
        
        return card_box

    def go_to_search_with_query(self, query):
        self.sidebar_list.select_row(self.row_search)
        self.search_entry.set_text(query)
        self.on_search_clicked(None)

    # --- 2. SEARCH PAGE ---

    def create_search_page(self):
        self.search_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Search panel Container
        search_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        search_panel.set_margin_top(16)
        search_panel.set_margin_bottom(12)
        search_panel.set_margin_start(24)
        search_panel.set_margin_end(24)
        
        # Title
        self.search_title = Gtk.Label()
        self.search_title.set_markup("<span size='large' weight='bold'>軟體搜尋</span>")
        self.search_title.set_halign(Gtk.Align.START)
        search_panel.append(self.search_title)
        
        # Search Box
        search_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("輸入關鍵字進行搜尋，例如：code, gimp, chrome...")
        self.search_entry.connect("activate", self.on_search_clicked)
        search_hbox.append(self.search_entry)
        
        self.btn_search = Gtk.Button(label="🔍 搜尋")
        self.btn_search.connect("clicked", self.on_search_clicked)
        search_hbox.append(self.btn_search)
        
        # One-Click Auto Install button
        self.btn_auto_install = Gtk.Button(label="⚡ 一鍵自動安裝")
        self.btn_auto_install.add_css_class("suggested-action")
        self.btn_auto_install.connect("clicked", self.on_auto_install_clicked)
        search_hbox.append(self.btn_auto_install)
        
        search_panel.append(search_hbox)
        
        # Filters CheckButtons (Flatpak unchecked by default)
        filter_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        filter_hbox.set_halign(Gtk.Align.START)
        
        self.filter_pacman = Gtk.CheckButton(label="官方倉庫 (Pacman)")
        self.filter_pacman.set_active(True)
        self.filter_aur = Gtk.CheckButton(label="使用者倉庫 (AUR)")
        self.filter_aur.set_active(True)
        self.filter_flatpak = Gtk.CheckButton(label="沙盒套件 (Flatpak)")
        self.filter_flatpak.set_active(False)
        self.filter_npm = Gtk.CheckButton(label="Node 套件 (npm)")
        self.filter_npm.set_active(True)
        
        filter_hbox.append(self.filter_pacman)
        filter_hbox.append(self.filter_aur)
        filter_hbox.append(self.filter_flatpak)
        filter_hbox.append(self.filter_npm)
        search_panel.append(filter_hbox)
        
        self.search_page.append(search_panel)
        
        # Results Section
        results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        results_box.set_vexpand(True)
        results_box.set_hexpand(True)
        results_box.set_margin_start(24)
        results_box.set_margin_end(24)
        results_box.set_margin_bottom(16)
        
        # Scroll Window for Results
        self.results_scroll = Gtk.ScrolledWindow()
        self.results_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.results_scroll.set_vexpand(True)
        
        # Results List Box
        self.results_listbox = Gtk.ListBox()
        self.results_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_scroll.set_child(self.results_listbox)
        
        # Loading Indicator & Status Label
        self.search_status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.search_status_box.set_valign(Gtk.Align.CENTER)
        self.search_status_box.set_halign(Gtk.Align.CENTER)
        self.search_status_box.set_vexpand(True)
        
        self.search_spinner = Gtk.Spinner()
        self.search_spinner.set_size_request(32, 32)
        self.search_status_box.append(self.search_spinner)
        
        self.search_status_label = Gtk.Label(label="輸入關鍵字，探索您的系統應用")
        self.search_status_box.append(self.search_status_label)
        
        results_box.append(self.search_status_box)
        results_box.append(self.results_scroll)
        
        # Default state: hide scroll results, show intro status
        self.results_scroll.set_visible(False)
        self.search_spinner.stop()
        
        self.search_page.append(results_box)

    # --- 3. INSTALLED PAGE ---

    def create_installed_page(self):
        self.installed_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.installed_page.set_margin_top(16)
        self.installed_page.set_margin_bottom(16)
        self.installed_page.set_margin_start(24)
        self.installed_page.set_margin_end(24)
        
        # Title and refresh top row
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.installed_title = Gtk.Label()
        self.installed_title.set_markup("<span size='large' weight='bold'>已安裝的軟體</span>")
        self.installed_title.set_hexpand(True)
        self.installed_title.set_halign(Gtk.Align.START)
        hbox_top.append(self.installed_title)
        
        self.btn_refresh_installed = Gtk.Button(label="🔄 重新整理")
        self.btn_refresh_installed.connect("clicked", lambda b: self.refresh_installed_list())
        hbox_top.append(self.btn_refresh_installed)
        self.installed_page.append(hbox_top)
        
        # Scrollable container
        self.installed_scroll = Gtk.ScrolledWindow()
        self.installed_scroll.set_hexpand(True)
        self.installed_scroll.set_vexpand(True)
        self.installed_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.installed_listbox = Gtk.ListBox()
        self.installed_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.installed_scroll.set_child(self.installed_listbox)
        self.installed_page.append(self.installed_scroll)

    def refresh_installed_list(self):
        thread = threading.Thread(target=self.load_installed_apps_thread)
        thread.daemon = True
        thread.start()
        
    def load_installed_apps_thread(self):
        from search import get_installed_pacman_packages_dict, get_installed_flatpaks_dict
        
        pacman_installed = get_installed_pacman_packages_dict()
        
        # Fetch explicitly installed pacman packages (clean user-facing list)
        explicit_installed = set()
        try:
            res = subprocess.run(
                ['pacman', '-Qeq'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res.returncode == 0:
                explicit_installed = set(line.strip() for line in res.stdout.split('\n') if line.strip())
        except Exception:
            pass
            
        # Fetch foreign packages (AUR/Local packages)
        foreign_installed = set()
        try:
            res_foreign = subprocess.run(
                ['pacman', '-Qmq'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res_foreign.returncode == 0:
                foreign_installed = set(line.strip() for line in res_foreign.stdout.split('\n') if line.strip())
        except Exception:
            pass
            
        packages = []
        # Filter pacman_installed to only show explicit ones, identifying AUR packages correctly
        for name, version in pacman_installed.items():
            if name in explicit_installed:
                is_aur = name in foreign_installed
                packages.append({
                    'name': name,
                    'app_id': name,
                    'version': version,
                    'source': 'AUR' if is_aur else 'Pacman',
                    'repo': 'installed',
                    'description': self.tr('desc_aur') if is_aur else self.tr('desc_pacman')
                })
                
        # Get flatpaks
        flatpaks = get_installed_flatpaks_dict()
        for app_id, version in flatpaks.items():
            packages.append({
                'name': app_id.split('.')[-1],
                'app_id': app_id,
                'version': version,
                'source': 'Flatpak',
                'repo': 'installed',
                'description': self.tr('desc_flatpak').format(app_id=app_id)
            })
            
        # Sort alphabetically
        packages.sort(key=lambda x: x['name'].lower())
        
        GLib.idle_add(self.show_installed_apps, packages)

    def show_installed_apps(self, packages):
        while True:
            child = self.installed_listbox.get_first_child()
            if child is None:
                break
            self.installed_listbox.remove(child)
            
        if not packages:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=self.tr('no_installed_packages'))
            lbl.set_margin_top(20)
            lbl.set_margin_bottom(20)
            row.set_child(lbl)
            self.installed_listbox.append(row)
            return
            
        for pkg in packages:
            row = Gtk.ListBoxRow()
            row.add_css_class("package-row")
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_top(6)
            hbox.set_margin_bottom(6)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            vbox.set_hexpand(True)
            
            title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            title_box.set_halign(Gtk.Align.START)
            
            name_lbl = Gtk.Label()
            name_lbl.set_markup(f"<b>{pkg['name']}</b>")
            title_box.append(name_lbl)
            
            badge = Gtk.Label(label=pkg['source'])
            badge.add_css_class("badge-label")
            if pkg['source'] == 'Pacman':
                badge.add_css_class("badge-pacman")
            elif pkg['source'] == 'AUR':
                badge.add_css_class("badge-aur")
            elif pkg['source'] == 'Flatpak':
                badge.add_css_class("badge-flatpak")
            title_box.append(badge)
            vbox.append(title_box)
            
            desc_lbl = Gtk.Label(label=f"版本: {pkg['version']} | {pkg['description']}")
            desc_lbl.set_halign(Gtk.Align.START)
            desc_lbl.add_css_class("dim-label")
            desc_lbl.set_wrap(True)
            desc_lbl.set_max_width_chars(60)
            vbox.append(desc_lbl)
            hbox.append(vbox)
            
            btn_uninstall = Gtk.Button(label="卸載")
            btn_uninstall.add_css_class("destructive-action")
            btn_uninstall.set_valign(Gtk.Align.CENTER)
            btn_uninstall.connect("clicked", lambda b, p=pkg: self.start_uninstallation(p))
            hbox.append(btn_uninstall)
            
            row.set_child(hbox)
            self.installed_listbox.append(row)

    # --- 4. UPDATES PAGE ---

    def create_updates_page(self):
        self.updates_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.updates_page.set_margin_top(16)
        self.updates_page.set_margin_bottom(16)
        self.updates_page.set_margin_start(24)
        self.updates_page.set_margin_end(24)
        
        # Title and action bar
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.updates_title = Gtk.Label()
        self.updates_title.set_markup("<span size='large' weight='bold'>系統更新與升級</span>")
        self.updates_title.set_hexpand(True)
        self.updates_title.set_halign(Gtk.Align.START)
        hbox_top.append(self.updates_title)
        
        self.btn_update_all = Gtk.Button(label="⚡ 全部更新")
        self.btn_update_all.add_css_class("suggested-action")
        self.btn_update_all.connect("clicked", lambda b: self.start_system_upgrade())
        hbox_top.append(self.btn_update_all)
        
        self.btn_check_updates = Gtk.Button(label="🔄 檢查更新")
        self.btn_check_updates.connect("clicked", lambda b: self.refresh_updates_list())
        hbox_top.append(self.btn_check_updates)
        self.updates_page.append(hbox_top)
        
        # Scroll Window
        self.updates_scroll = Gtk.ScrolledWindow()
        self.updates_scroll.set_hexpand(True)
        self.updates_scroll.set_vexpand(True)
        self.updates_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.updates_listbox = Gtk.ListBox()
        self.updates_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.updates_scroll.set_child(self.updates_listbox)
        self.updates_page.append(self.updates_scroll)

    def check_updates_startup(self):
        thread = threading.Thread(target=self.load_updates_silent_thread)
        thread.daemon = True
        thread.start()
        return False # Run once

    def load_updates_silent_thread(self):
        updates = []
        try:
            res = subprocess.run(
                ['yay', '-Qu'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res.returncode == 0 or res.returncode == 1:
                for line in res.stdout.split('\n'):
                    if not line.strip():
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[2] == '->':
                        updates.append(parts[0])
        except Exception:
            pass
            
        try:
            res_npm = subprocess.run(
                ['npm', 'outdated', '-g', '--json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res_npm.stdout.strip():
                data = json.loads(res_npm.stdout)
                updates.extend(list(data.keys()))
        except Exception:
            pass
            
        GLib.idle_add(self.update_sidebar_badge, len(updates))

    def update_sidebar_badge(self, count):
        if count > 0:
            self.updates_badge_label.set_text(str(count))
            self.updates_badge_label.set_visible(True)
        else:
            self.updates_badge_label.set_visible(False)

    def refresh_updates_list(self):
        self.btn_update_all.set_sensitive(False)
        thread = threading.Thread(target=self.load_updates_thread)
        thread.daemon = True
        thread.start()
        
    def load_updates_thread(self):
        updates = []
        try:
            res = subprocess.run(
                ['yay', '-Qu'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res.returncode == 0 or res.returncode == 1:
                for line in res.stdout.split('\n'):
                    if not line.strip():
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[2] == '->':
                        name = parts[0]
                        old_ver = parts[1]
                        new_ver = parts[3]
                        
                        updates.append({
                            'name': name,
                            'old_version': old_ver,
                            'new_version': new_ver,
                            'source': 'AUR' if 'aur' in name or not self.is_official_repo_package(name) else 'Pacman'
                        })
        except Exception as e:
            print(f"Error checking native updates: {e}")
            
        try:
            res_npm = subprocess.run(
                ['npm', 'outdated', '-g', '--json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if res_npm.stdout.strip():
                data = json.loads(res_npm.stdout)
                for name, info in data.items():
                    updates.append({
                        'name': name,
                        'old_version': info.get('current', ''),
                        'new_version': info.get('latest', ''),
                        'source': 'npm'
                    })
        except Exception as e:
            print(f"Error checking npm updates: {e}")
            
        GLib.idle_add(self.show_updates, updates)
        
    def is_official_repo_package(self, name):
        try:
            res = subprocess.run(
                ['pacman', '-Si', name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return res.returncode == 0
        except Exception:
            return False

    def show_updates(self, updates):
        while True:
            child = self.updates_listbox.get_first_child()
            if child is None:
                break
            self.updates_listbox.remove(child)
            
        # Update badge count in sidebar
        self.update_sidebar_badge(len(updates))
        if len(updates) > 0:
            self.btn_update_all.set_sensitive(True)
        else:
            self.btn_update_all.set_sensitive(False)
            
        if not updates:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=self.tr('system_up_to_date'))
            lbl.set_margin_top(20)
            lbl.set_margin_bottom(20)
            row.set_child(lbl)
            self.updates_listbox.append(row)
            return
            
        for upg in updates:
            row = Gtk.ListBoxRow()
            row.add_css_class("package-row")
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_top(6)
            hbox.set_margin_bottom(6)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            vbox.set_hexpand(True)
            
            title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            title_box.set_halign(Gtk.Align.START)
            
            name_lbl = Gtk.Label()
            name_lbl.set_markup(f"<b>{upg['name']}</b>")
            title_box.append(name_lbl)
            
            badge = Gtk.Label(label=upg['source'])
            badge.add_css_class("badge-label")
            if upg['source'] == 'Pacman':
                badge.add_css_class("badge-pacman")
            elif upg['source'] == 'AUR':
                badge.add_css_class("badge-aur")
            elif upg['source'] == 'Flatpak':
                badge.add_css_class("badge-flatpak")
            elif upg['source'] == 'npm':
                badge.add_css_class("badge-npm")
            title_box.append(badge)
            vbox.append(title_box)
            
            desc_lbl = Gtk.Label(label=self.tr('update_detail').format(old=upg['old_version'], new=upg['new_version']))
            desc_lbl.set_halign(Gtk.Align.START)
            desc_lbl.add_css_class("dim-label")
            vbox.append(desc_lbl)
            hbox.append(vbox)
            
            btn_upgrade = Gtk.Button(label=self.tr('btn_upgrade_single'))
            btn_upgrade.add_css_class("suggested-action")
            btn_upgrade.set_valign(Gtk.Align.CENTER)
            btn_upgrade.connect("clicked", lambda b, u=upg: self.start_single_upgrade(u))
            hbox.append(btn_upgrade)
            
            row.set_child(hbox)
            self.updates_listbox.append(row)

    # --- 5. INSTALLATION / PROGRESS PAGE ---

    def create_install_page(self):
        self.install_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.install_page.set_margin_top(24)
        self.install_page.set_margin_bottom(24)
        self.install_page.set_margin_start(24)
        self.install_page.set_margin_end(24)
        
        # Title Box
        self.install_title = Gtk.Label()
        self.install_title.set_markup("<span size='large' weight='bold'>正在執行操作...</span>")
        self.install_title.set_halign(Gtk.Align.START)
        self.install_page.append(self.install_title)
        
        # Loader Spinner and Sub-status Box
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.install_spinner = Gtk.Spinner()
        self.install_spinner.set_size_request(24, 24)
        status_box.append(self.install_spinner)
        
        self.install_status_label = Gtk.Label(label="正在準備...")
        status_box.append(self.install_status_label)
        self.install_page.append(status_box)
        
        # Modern console output view
        self.terminal_scroll = Gtk.ScrolledWindow()
        self.terminal_scroll.set_vexpand(True)
        self.terminal_scroll.set_hexpand(True)
        self.terminal_scroll.add_css_class("terminal-scroll")
        
        self.terminal_view = Gtk.TextView()
        self.terminal_view.set_editable(False)
        self.terminal_view.set_cursor_visible(False)
        self.terminal_view.set_margin_top(8)
        self.terminal_view.set_margin_bottom(8)
        self.terminal_view.set_margin_start(12)
        self.terminal_view.set_margin_end(12)
        self.terminal_view.add_css_class("terminal-view")
        
        self.terminal_scroll.set_child(self.terminal_view)
        self.install_page.append(self.terminal_scroll)
        
        # Navigation Buttons (Cancel & Back)
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_box.set_halign(Gtk.Align.END)
        
        self.btn_cancel_install = Gtk.Button(label="取消")
        self.btn_cancel_install.add_css_class("destructive-action")
        self.btn_cancel_install.connect("clicked", self.on_cancel_install_clicked)
        actions_box.append(self.btn_cancel_install)
        
        self.btn_back_to_search = Gtk.Button(label="返回首頁")
        self.btn_back_to_search.connect("clicked", self.on_back_to_search_clicked)
        self.btn_back_to_search.set_sensitive(False)
        actions_box.append(self.btn_back_to_search)
        
        self.install_page.append(actions_box)

    # --- UI EVENT HANDLERS ---

    def create_package_row(self, pkg):
        row = Gtk.ListBoxRow()
        row.add_css_class("package-row")
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        hbox.set_margin_start(12)
        hbox.set_margin_end(12)
        
        # Left Side Info Box
        vbox_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox_info.set_hexpand(True)
        
        # Name and badges row
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.set_halign(Gtk.Align.START)
        
        name_lbl = Gtk.Label()
        name_lbl.set_markup(f"<b>{pkg['name']}</b>")
        name_lbl.set_halign(Gtk.Align.START)
        title_box.append(name_lbl)
        
        badge_lbl = Gtk.Label(label=pkg['source'])
        badge_lbl.set_valign(Gtk.Align.CENTER)
        badge_lbl.add_css_class("badge-label")
        if pkg['source'] == 'Pacman':
            badge_lbl.add_css_class("badge-pacman")
        elif pkg['source'] == 'AUR':
            badge_lbl.add_css_class("badge-aur")
        elif pkg['source'] == 'Flatpak':
            badge_lbl.add_css_class("badge-flatpak")
        elif pkg['source'] == 'npm':
            badge_lbl.add_css_class("badge-npm")
        title_box.append(badge_lbl)
        
        if pkg['installed']:
            if pkg.get('has_update'):
                inst_lbl = Gtk.Label(label=self.tr('label_has_update').format(version=pkg.get('installed_version', '')))
                inst_lbl.add_css_class("warning-label")
            else:
                inst_lbl = Gtk.Label(label=self.tr('label_installed'))
                inst_lbl.add_css_class("success-label")
            title_box.append(inst_lbl)
            
        vbox_info.append(title_box)
        
        # Description
        desc_text = pkg['description'] or self.tr('no_description')
        desc_lbl = Gtk.Label(label=desc_text)
        desc_lbl.set_wrap(True)
        desc_lbl.set_max_width_chars(65)
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.add_css_class("dim-label")
        vbox_info.append(desc_lbl)
        
        # Version and Repo details
        details = self.tr('pkg_details').format(version=pkg['version'], repo=pkg['repo'])
        details_lbl = Gtk.Label(label=details)
        details_lbl.set_halign(Gtk.Align.START)
        details_lbl.add_css_class("small-label")
        vbox_info.append(details_lbl)
        
        hbox.append(vbox_info)
        
        # Install Action Button
        btn_action = Gtk.Button()
        if pkg['installed']:
            if pkg.get('has_update'):
                btn_action.set_label(self.tr('btn_update_pkg'))
                btn_action.add_css_class("suggested-action")
            else:
                btn_action.set_label(self.tr('btn_reinstall_pkg'))
                btn_action.add_css_class("flat")
        else:
            btn_action.set_label(self.tr('btn_install_pkg'))
            btn_action.add_css_class("suggested-action")
            
        btn_action.set_valign(Gtk.Align.CENTER)
        btn_action.connect("clicked", lambda b: self.start_installation(pkg))
        hbox.append(btn_action)
        
        row.set_child(hbox)
        return row

    def on_search_clicked(self, widget):
        query = self.search_entry.get_text().strip()
        if not query:
            return
            
        # Switch GUI to loading state
        self.results_scroll.set_visible(False)
        self.search_status_box.set_visible(True)
        self.search_spinner.start()
        self.search_status_label.set_text(f"正在搜尋 '{query}'，請稍候...")
        
        # Trigger async search thread
        thread = threading.Thread(target=self.run_search_thread, args=(query,))
        thread.daemon = True
        thread.start()

    def run_search_thread(self, query):
        try:
            show_pacman = self.filter_pacman.get_active()
            show_aur = self.filter_aur.get_active()
            show_flatpak = self.filter_flatpak.get_active()
            show_npm = self.filter_npm.get_active()
            
            results = search_all(query, show_pacman, show_aur, show_flatpak, show_npm)
            
            filtered = []
            for r in results:
                if r['source'] == 'Pacman' and not show_pacman:
                    continue
                if r['source'] == 'AUR' and not show_aur:
                    continue
                if r['source'] == 'Flatpak' and not show_flatpak:
                    continue
                if r['source'] == 'npm' and not show_npm:
                    continue
                filtered.append(r)
                
            GLib.idle_add(self.on_search_completed, filtered)
        except Exception as e:
            print(f"Error in search thread: {e}")

    def on_search_completed(self, results):
        self.search_spinner.stop()
        
        # Clear previous ListBox rows
        while True:
            child = self.results_listbox.get_first_child()
            if child is None:
                break
            self.results_listbox.remove(child)
            
        if not results:
            self.search_status_box.set_visible(True)
            self.search_status_label.set_text("找不到符合條件的套件。請嘗試其他關鍵字！")
            self.results_scroll.set_visible(False)
            return
            
        # Append new results
        for pkg in results:
            row = self.create_package_row(pkg)
            self.results_listbox.append(row)
            
        # Display listbox
        self.search_status_box.set_visible(False)
        self.results_scroll.set_visible(True)

    def on_auto_install_clicked(self, widget):
        query = self.search_entry.get_text().strip()
        if not query:
            return
            
        self.clear_terminal()
        self.install_title.set_markup(f"<span size='large' weight='bold'>⚡ 自動安裝: {query}</span>")
        self.install_status_label.set_text("搜尋匹配的套件中...")
        self.install_spinner.start()
        self.btn_cancel_install.set_sensitive(True)
        self.btn_cancel_install.set_visible(True)
        self.btn_back_to_search.set_sensitive(False)
        
        # Switch to install view
        self.main_stack.set_visible_child_name("install_page")
        self.should_cancel = False
        
        thread = threading.Thread(target=self.run_auto_install_pipeline_thread, args=(query,))
        thread.daemon = True
        thread.start()

    def run_auto_install_pipeline_thread(self, query):
        self.append_terminal_line(f"===> 啟動自動安裝程序，搜尋關鍵字: '{query}'\n")
        
        # 1. Search for exact case-insensitive matches first
        self.update_status_idle("正在檢索最佳套件...")
        results = search_all(query)
        exact_match = None
        for r in results:
            if r['name'].lower() == query.lower() or r.get('app_id', '').lower() == query.lower():
                exact_match = r
                break
                
        if exact_match:
            self.append_terminal_line(f"[+] 找到完全匹配的套件：{exact_match['name']} ({exact_match['source']})，直接執行安裝管道。\n")
            if exact_match['source'] == 'Pacman':
                cmd = ["pkexec", "pacman", "-S", "--noconfirm", exact_match['name']]
            elif exact_match['source'] == 'AUR':
                cmd = ["yay", "-S", "--noconfirm", exact_match['name']]
            else:
                cmd = ["flatpak", "install", "-y", "flathub", exact_match['app_id']]
                
            success = self.execute_install_command(cmd, exact_match['source'])
            if success:
                self.finish_installation(True, f"成功安裝 '{exact_match['name']}'。")
            else:
                self.finish_installation(False, f"安裝 '{exact_match['name']}' 失敗。")
            return
            
        # 2. Check Pacman
        self.update_status_idle("正在檢查 Pacman 官方軟體庫...")
        self.append_terminal_line(f"[*] 正在官方 Pacman 軟體庫中搜尋 '{query}'...\n")
        
        pacman_check = subprocess.run(
            ["pacman", "-Si", query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if pacman_check.returncode == 0:
            self.append_terminal_line(f"[+] 找到官方軟體包：'{query}'。準備使用 Pacman 安裝。\n")
            cmd = ["pkexec", "pacman", "-S", "--noconfirm", query]
            success = self.execute_install_command(cmd, "Pacman (系統管理員)")
            if success:
                self.finish_installation(True, f"成功透過 Pacman 安裝 '{query}'。")
                return
            else:
                self.append_terminal_line("[-] Pacman 安裝失敗。嘗試備用安裝方案...\n")
        else:
            self.append_terminal_line(f"[-] 官方軟體庫中找不到 '{query}'。\n")
            
        if self.should_cancel:
            self.finish_installation(False, "安裝被使用者取消。")
            return
            
        # 3. Check AUR
        self.update_status_idle("正在檢查 AUR 社群軟體庫...")
        self.append_terminal_line(f"[*] 正在 AUR (Arch User Repository) 中搜尋 '{query}'...\n")
        
        aur_check = subprocess.run(
            ["yay", "-Si", query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if aur_check.returncode == 0:
            self.append_terminal_line(f"[+] 找到 AUR 社群軟體包：'{query}'。準備使用 yay 編譯安裝。\n")
            cmd = ["yay", "-S", "--noconfirm", query]
            success = self.execute_install_command(cmd, "yay (AUR 套件管理員)")
            if success:
                self.finish_installation(True, f"成功透過 AUR 安裝 '{query}'。")
                return
            else:
                self.append_terminal_line("[-] AUR 安裝失敗。嘗試備用安裝方案...\n")
        else:
            self.append_terminal_line(f"[-] AUR 中找不到 '{query}'。\n")
 
        if self.should_cancel:
            self.finish_installation(False, "安裝被使用者取消。")
            return
 
        # 4. Check Flatpak
        self.update_status_idle("正在檢查 Flatpak (Flathub) 軟體庫...")
        self.append_terminal_line(f"[*] 正在 Flathub 中搜尋 '{query}'...\n")
        
        flatpak_search = subprocess.run(
            ["flatpak", "search", query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if flatpak_search.returncode == 0 and flatpak_search.stdout.strip():
            lines = flatpak_search.stdout.split('\n')
            app_id = None
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 3:
                    candidate_id = parts[2].strip()
                    if query.lower() in candidate_id.lower():
                        app_id = candidate_id
                        break
            
            if not app_id and len(lines) > 0:
                parts = lines[0].split('\t')
                if len(parts) >= 3:
                    app_id = parts[2].strip()
                    
            if app_id:
                self.append_terminal_line(f"[+] 找到 Flatpak 套件：'{app_id}'。準備安裝。\n")
                cmd = ["flatpak", "install", "-y", "flathub", app_id]
                success = self.execute_install_command(cmd, "Flatpak")
                if success:
                    self.finish_installation(True, f"成功透過 Flatpak 安裝 '{app_id}'。")
                    return
                else:
                    self.append_terminal_line("[-] Flatpak 安裝失敗。\n")
            else:
                self.append_terminal_line("[-] 無法解析 Flatpak Application ID。\n")
        else:
            self.append_terminal_line(f"[-] Flatpak 中找不到 '{query}'。\n")
            
        self.finish_installation(False, f"自動安裝失敗：在 Pacman, AUR 及 Flatpak 中皆找不到或無法安裝 '{query}'。")

    # --- CORE INSTALLATION & UNINSTALLATION WORKERS ---

    def start_installation(self, pkg):
        self.clear_terminal()
        self.install_title.set_markup(f"<span size='large' weight='bold'>正在安裝: {pkg['name']}</span>")
        self.install_status_label.set_text("準備中...")
        self.install_spinner.start()
        
        self.btn_cancel_install.set_sensitive(True)
        self.btn_cancel_install.set_visible(True)
        self.btn_back_to_search.set_sensitive(False)
        
        # Switch to progress view
        self.main_stack.set_visible_child_name("install_page")
        self.should_cancel = False
        
        if pkg['source'] == 'Pacman':
            cmd = ["pkexec", "pacman", "-S", "--noconfirm", pkg['name']]
        elif pkg['source'] == 'AUR':
            cmd = ["yay", "-S", "--noconfirm", pkg['name']]
        elif pkg['source'] == 'Flatpak':
            cmd = ["flatpak", "install", "-y", "flathub", pkg['app_id']]
        elif pkg['source'] == 'npm':
            cmd = ["sudo", "-A", "npm", "install", "-g", pkg['name']]
            
        thread = threading.Thread(
            target=self.run_install_thread, 
            args=(cmd, pkg['name'], pkg['source']), 
            daemon=True
        )
        thread.start()

    def start_uninstallation(self, pkg):
        self.clear_terminal()
        self.install_title.set_markup(f"<span size='large' weight='bold'>正在卸載: {pkg['name']}</span>")
        self.install_status_label.set_text("準備卸載中...")
        self.install_spinner.start()
        
        # Cannot cancel uninstalls easily, hide cancel button
        self.btn_cancel_install.set_sensitive(False)
        self.btn_cancel_install.set_visible(False)
        self.btn_back_to_search.set_sensitive(False)
        
        # Switch to progress view
        self.main_stack.set_visible_child_name("install_page")
        
        if pkg['source'] == 'Flatpak':
            cmd = ["flatpak", "uninstall", "-y", pkg['app_id']]
        elif pkg['source'] == 'npm':
            cmd = ["sudo", "-A", "npm", "uninstall", "-g", pkg['name']]
        else:
            cmd = ["pkexec", "pacman", "-Rns", "--noconfirm", pkg['name']]
            
        thread = threading.Thread(
            target=self.run_uninstall_thread,
            args=(cmd, pkg['name'], pkg['source']),
            daemon=True
        )
        thread.start()

    def start_single_upgrade(self, upg):
        self.clear_terminal()
        self.install_title.set_markup(f"<span size='large' weight='bold'>正在升級: {upg['name']}</span>")
        self.install_status_label.set_text("準備升級中...")
        self.install_spinner.start()
        
        self.btn_cancel_install.set_sensitive(True)
        self.btn_cancel_install.set_visible(True)
        self.btn_back_to_search.set_sensitive(False)
        self.main_stack.set_visible_child_name("install_page")
        self.should_cancel = False
        
        if upg['source'] == 'Pacman':
            cmd = ["pkexec", "pacman", "-S", "--noconfirm", upg['name']]
        elif upg['source'] == 'npm':
            cmd = ["sudo", "-A", "npm", "install", "-g", upg['name']]
        else:
            cmd = ["yay", "-S", "--noconfirm", upg['name']]
            
        thread = threading.Thread(
            target=self.run_install_thread,
            args=(cmd, upg['name'], upg['source']),
            daemon=True
        )
        thread.start()

    def start_system_upgrade(self):
        self.clear_terminal()
        self.install_title.set_markup(f"<span size='large' weight='bold'>正在執行系統全量升級</span>")
        self.install_status_label.set_text("全系統升級中...")
        self.install_spinner.start()
        
        self.btn_cancel_install.set_sensitive(True)
        self.btn_cancel_install.set_visible(True)
        self.btn_back_to_search.set_sensitive(False)
        self.main_stack.set_visible_child_name("install_page")
        self.should_cancel = False
        
        cmd = ["yay", "-Syu", "--noconfirm"]
        
        thread = threading.Thread(
            target=self.run_install_thread,
            args=(cmd, "系統全量升級", "yay (全系統)"),
            daemon=True
        )
        thread.start()

    def run_install_thread(self, cmd, pkg_name, source):
        self.update_status_idle(f"正在執行 {source} 安裝指令...")
        success = self.execute_install_command(cmd, source)
        if success:
            self.finish_installation(True, f"成功安裝 '{pkg_name}'。")
        else:
            self.finish_installation(False, f"安裝 '{pkg_name}' 失敗。")

    def run_uninstall_thread(self, cmd, pkg_name, source):
        self.update_status_idle(f"正在執行 {source} 卸載指令...")
        success = self.execute_install_command(cmd, source)
        if success:
            self.finish_installation(True, f"成功卸載 '{pkg_name}'。")
        else:
            self.finish_installation(False, f"卸載 '{pkg_name}' 失敗。")

    def execute_install_command(self, cmd, source):
        # Configure ASKPASS for yay/AUR prompts
        script_dir = os.path.dirname(os.path.abspath(__file__))
        askpass_path = os.path.join(script_dir, "askpass.py")
            
        env = os.environ.copy()
        env["SUDO_ASKPASS"] = askpass_path
        
        # Safety Check: Verify that the tool executable is installed
        import shutil
        tool_exec = cmd[2] if cmd[0] == "sudo" else (cmd[1] if cmd[0] == "pkexec" else cmd[0])
        if not shutil.which(tool_exec):
            self.append_terminal_line(f"[-] 錯誤：系統找不到可執行檔 '{tool_exec}'。\n")
            self.append_terminal_line(f"[-] 請先手動安裝它！例如使用 Pacman 安裝：sudo pacman -S {tool_exec}\n")
            return False
        
        # Pre-authenticate sudo for yay/AUR and sudo commands to prevent password prompts mid-build
        if cmd[0] == "yay" or cmd[0] == "sudo":
            self.update_status_idle("正在驗證管理員權限...")
            self.append_terminal_line("[*] 正在驗證管理員授權以利後續自動安裝...\n")
            pre_auth_res = subprocess.run(
                ["sudo", "-v"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if pre_auth_res.returncode != 0:
                self.append_terminal_line("[-] 管理員授權失敗，取消安裝。\n")
                return False
            self.append_terminal_line("[+] 授權成功，開始編譯與安裝。\n")
            
        self.append_terminal_line(f"===> 啟動：{' '.join(cmd)}\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            while True:
                if self.should_cancel:
                    self.append_terminal_line("\n[!] 偵測到使用者點擊取消。正在強制中斷子程序...\n")
                    process.terminate()
                    process.wait()
                    return False
                    
                line = process.stdout.readline()
                if not line:
                    break
                    
                self.append_terminal_line(line)
                
                # Dynamic terminal parser update
                if "loading packages" in line.lower() or "downloading" in line.lower():
                    self.update_status_idle("正在下載與快取軟體包...")
                elif "checking keys" in line.lower() or "checking integrity" in line.lower():
                    self.update_status_idle("正在檢查軟體包金鑰及完整性...")
                elif "installing" in line.lower() or "upgrading" in line.lower():
                    self.update_status_idle("正在複製檔案並配置系統...")
                    
            process.wait()
            return process.returncode == 0
            
        except Exception as e:
            self.append_terminal_line(f"執行出錯: {e}\n")
            return False

    def handle_argument(self, arg):
        if os.path.exists(arg):
            abs_path = os.path.abspath(arg)
            filename = os.path.basename(abs_path)
            
            # Local pkg files
            if abs_path.endswith(('.pkg.tar.zst', '.pkg.tar.xz', '.pkg.tar.gz')):
                self.install_title.set_markup(f"<span size='large' weight='bold'>安裝 Pacman 本地套件: {filename}</span>")
                self.install_status_label.set_text("準備安裝本地檔...")
                self.install_spinner.start()
                self.btn_cancel_install.set_sensitive(True)
                self.btn_cancel_install.set_visible(True)
                self.btn_back_to_search.set_sensitive(False)
                self.main_stack.set_visible_child_name("install_page")
                self.should_cancel = False
                
                cmd = ["pkexec", "pacman", "-U", "--noconfirm", abs_path]
                thread = threading.Thread(
                    target=self.run_install_thread, 
                    args=(cmd, filename, "Pacman (本地檔)"), 
                    daemon=True
                )
                thread.start()
                
            # Local flatpak files
            elif abs_path.endswith(('.flatpak', '.flatpakref')):
                self.install_title.set_markup(f"<span size='large' weight='bold'>安裝 Flatpak 本地套件: {filename}</span>")
                self.install_status_label.set_text("準備安裝本地檔...")
                self.install_spinner.start()
                self.btn_cancel_install.set_sensitive(True)
                self.btn_cancel_install.set_visible(True)
                self.btn_back_to_search.set_sensitive(False)
                self.main_stack.set_visible_child_name("install_page")
                self.should_cancel = False
                
                cmd = ["flatpak", "install", "-y", abs_path]
                thread = threading.Thread(
                    target=self.run_install_thread, 
                    args=(cmd, filename, "Flatpak (本地檔)"), 
                    daemon=True
                )
                thread.start()
        else:
            # Command line package query redirect
            self.sidebar_list.select_row(self.row_search)
            self.search_entry.set_text(arg)
            self.on_search_clicked(None)

    def on_cancel_install_clicked(self, widget):
        self.should_cancel = True
        self.btn_cancel_install.set_sensitive(False)
        self.install_status_label.set_text("正在取消中...")

    def on_back_to_search_clicked(self, widget):
        self.btn_back_to_search.set_sensitive(False)
        
        # Force a selection change signal trigger by deselecting first
        self.sidebar_list.select_row(None)
        self.sidebar_list.select_row(self.row_installed)
        
        # Silently trigger background update check to keep updates badge current
        self.check_updates_startup()

    def clear_terminal(self):
        buffer = self.terminal_view.get_buffer()
        buffer.set_text("")

    def append_terminal_line(self, line):
        # Thread-safe terminal buffer update via GLib.idle_add to prevent GTK 4 crashes
        def idle_append():
            buffer = self.terminal_view.get_buffer()
            end_iter = buffer.get_end_iter()
            buffer.insert(end_iter, line)
            
            adj = self.terminal_scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())
            return False
        
        GLib.idle_add(idle_append)

    def update_status_idle(self, text):
        GLib.idle_add(self.install_status_label.set_text, text)

    def finish_installation(self, success, message):
        def idle_finish():
            self.install_spinner.stop()
            self.btn_cancel_install.set_visible(False)
            self.btn_back_to_search.set_sensitive(True)
            
            if success:
                self.install_status_label.set_markup(f"<span color='#2ec27e' weight='bold'>{message}</span>")
                self.append_terminal_line("\n[+] 任務結束：操作成功。\n")
            else:
                self.install_status_label.set_markup(f"<span color='#e66100' weight='bold'>{message}</span>")
                self.append_terminal_line("\n[-] 任務結束：操作失敗或被中斷。\n")
        GLib.idle_add(idle_finish)

class AppInstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.rendy.arch.appinstaller',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = AppInstallerWindow(self)
        
        if len(sys.argv) > 1:
            file_or_pkg = sys.argv[1]
            win.handle_argument(file_or_pkg)
            
        win.present()

if __name__ == "__main__":
    app = AppInstallerApp()
    sys.exit(app.run([]))
