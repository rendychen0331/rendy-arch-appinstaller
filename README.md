# Dolphin ArchLinux App Installer (Linux 軟體套件安裝器)

基於 **Python + GTK 4 + Libadwaita** 開發的 Linux 視覺化套件安裝器。此工具旨在解決 Linux 安裝軟體需要頻繁輸入指令的痛點，整合官方 `pacman`、社群 `AUR (yay)` 及沙盒 `Flatpak` 軟體源，提供現代、簡潔且極致精美的圖形介面與「一鍵自動安裝」功能。

## ✨ 核心特色

1. **多來源智慧檢索**：同時搜尋 Arch 官方套件庫 (`pacman`)、Arch 使用者倉庫 (`AUR`) 及 Flatpak，顯示版本號與描述，並提供來源分類標籤。
2. **⚡ 一鍵自動智慧安裝**：輸入套件名稱後，程式將自動分析並按照最優優先級：**Pacman ➔ AUR ➔ Flatpak** 依序嘗試各類安裝指令，完全無需手動介入。
3. **終端機進度即時串流**：以極具質感的 VS Code 風格深色終端面板，即時呈現底層安裝指令的標準輸出與錯誤日誌，並支援平滑自動滾動。
4. **安全圖形化權限請求**：當需要管理員權限時，自動叫用系統原生 Polkit 授權彈窗（針對 Pacman 與 Flatpak 任務），或由程式彈出專屬 Libadwaita 密碼輸入框（針對 AUR 任務），免去終端機輸入密碼的麻煩。
5. **本地套件點擊安裝**：支援開啟本地 `.pkg.tar.zst` 等 Arch 套件檔或 `.flatpak` 檔案並呼叫 GUI 進行安裝。
6. **KDE Dolphin 右鍵選單深度整合**：
   - 右鍵點擊支援的套件檔案：顯示 **「使用 GUI 安裝套件」**
   - 右鍵點擊任何資料夾或空白處：顯示 **「開啟 Linux 套件安裝器」**

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

* [main.py](file:///home/rendy/Projects/dolphin-archlinux-appinstaller/main.py) ：GUI 主程式（主視窗、一鍵自動安裝流程控制、異步線程、終端日誌顯示、事件綁定）。
* [search.py](file:///home/rendy/Projects/dolphin-archlinux-appinstaller/search.py) ：軟體源搜尋與解析模組（包攬 `yay` 及 `flatpak` 指令的非同步搜尋與解析）。
* [askpass.py](file:///home/rendy/Projects/dolphin-archlinux-appinstaller/askpass.py) ：SUDO_ASKPASS 現代化圖形密碼視窗（透過 Libadwaita 彈出密碼輸入框以支援 AUR 安裝）。

---

## 🚀 安裝與執行

### 1. 本地啟動
您可以直接在專案目錄下執行：
```bash
python main.py
```

### 2. 命令行封裝 (CLI Wrapper)
我們已將啟動包裝放置於您個人的環境目錄：
* 執行檔路徑：`~/.local/bin/arch-app-installer`
現在您可在終端機直接輸入以下指令開啟：
```bash
arch-app-installer
```
或者直接傳遞參數進行自動安裝：
```bash
arch-app-installer gimp
```

### 3. Dolphin 右鍵選單整合與桌面選單
本專案已自動在以下目錄寫入整合配置：
* 系統應用程式選單：`~/.local/share/applications/arch-app-installer.desktop`
* Dolphin 右鍵選單 (KDE 5 & 6)：
  - `~/.local/share/kio/servicemenus/`
  - `~/.local/share/kservices5/ServiceMenus/`
