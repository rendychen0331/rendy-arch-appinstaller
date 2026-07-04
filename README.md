# rendy-arch-appinstaller (Linux 軟體套件安裝器)

基於 **Python + GTK 4 + Libadwaita** 開發的 Arch Linux 視覺化套件安裝器與管理器。此工具旨在解決 Linux 安裝軟體需要頻繁輸入指令的痛點，整合官方 `pacman`、社群 `AUR (yay)` 及沙盒 `Flatpak` 軟體源，提供現代、簡潔且極致精美的圖形介面與「一鍵自動安裝」功能。

## ✨ 核心特色

1. **📦 已安裝管理首頁**：開啟程式即顯示本機已安裝的套件列表（依 Pacman、AUR、Flatpak 分類並顯示對應標籤），方便進行搜尋與一鍵卸載。
2. **🔍 多來源智慧檢索**：同時搜尋 Arch 官方套件庫 (`pacman`)、Arch 使用者倉庫 (`AUR`) 及 Flatpak，顯示版本號與描述，並提供來源分類標籤。
3. **⚡ 一鍵自動智慧安裝**：輸入套件名稱後，程式將自動分析並按照最優優先級：**Pacman ➔ AUR ➔ Flatpak** 依序嘗試各類安裝指令，完全無需手動介入。
4. **📟 終端機進度即時串流**：以極具質感的 VS Code 風格深色終端面板，即時呈現底層安裝與編譯指令的標準輸出與錯誤日誌，並支援平滑自動滾動與執行緒安全防護。
5. **🛡️ 預先管理員提權**：安裝 AUR 套件時，程式會在一開始預先進行 `sudo -v` 驗證，並使用內建的 Python 圖形密碼視窗 (`askpass.py`) 接收密碼。輸入一次後即可享有 15 分鐘快取，讓漫長的 AUR 編譯與安裝流程全程自動化，免去中途彈出密碼的困擾。
6. **🐬 KDE Dolphin 右鍵選單整合**：
   - 右鍵點擊支援的套件檔案（如 `.pkg.tar.zst` 或 `.flatpak`）：顯示 **「使用 GUI 安裝套件」**

---

## 🛠️ 相依套件與系統需求

本程式在 Arch Linux 下運行，需具備以下套件：
* `python` (Python 3.x)
* `python-gobject` (PyGObject GTK 4 綁定)
* `gtk4` (GTK 4 核心庫)
* `libadwaita` (Adwaita 設計風格組件庫)
* `yay` (AUR 助手)
* `flatpak` (可選，用於 Flatpak 支援)

安裝相依指令：
```bash
sudo pacman -S python python-gobject gtk4 libadwaita yay flatpak
```

---

## 📂 檔案目錄結構

* `main.py` ：GUI 主程式（主視窗、一鍵自動安裝流程控制、異步執行緒、終端日誌顯示、事件綁定）。
* `search.py` ：軟體源搜尋與解析模組（包攬 `yay` 及 `flatpak` 指令的非同步搜尋與解析，支援空白字元及連字號變體檢索）。
* `askpass.py` ：SUDO_ASKPASS 現代化圖形密碼視窗（透過 Libadwaita 彈出密碼輸入框以支援 AUR 安裝）。
* `PKGBUILD` ：Arch 官方打包設定檔。
* `rendy-arch-appinstaller` ：二進位啟動包裝腳本。

---

## 🚀 安裝與執行

### 1. 使用 Arch PKGBUILD 進行安裝 (推薦)
在專案根目錄下，執行以下命令直接打包並安裝至系統：
```bash
makepkg -si
```
安裝完成後，軟體將自動註冊於系統中，您可以直接透過應用程式選單啟動它，或是透過終端機執行指令。

### 2. 終端機執行指令
您可以直接在終端機輸入以下指令啟動：
```bash
rendy-arch-appinstaller
```
或者直接傳遞參數進行自動安裝：
```bash
rendy-arch-appinstaller google-chrome
```

### 3. Dolphin 右鍵選單整合與桌面選單
系統安裝完畢後，軟體會自動在以下系統目錄寫入配置：
* 系統應用程式選單：`/usr/share/applications/org.rendy.arch.appinstaller.desktop`
* Dolphin 右鍵選單：
  - `/usr/share/kio/servicemenus/rendy-arch-appinstaller-file.desktop`
