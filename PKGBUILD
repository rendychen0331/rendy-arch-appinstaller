# Maintainer: rendy <rendy@example.com>
pkgname=arch-app-installer
pkgver=1.0.0
pkgrel=1
pkgdesc="基於 GTK 4 + Libadwaita 的視覺化套件安裝器與已安裝軟體管理器，支援 Pacman、AUR 及 Flatpak"
arch=('any')
url="https://github.com/rendy/arch-app-installer"
license=('GPL3')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'yay' 'flatpak')
source=('main.py'
        'search.py'
        'askpass.py'
        'arch-app-installer'
        'org.rendy.arch.appinstaller.desktop'
        'arch-app-installer-file.desktop'
        'arch-app-installer-folder.desktop')
sha256sums=('SKIP'
            'SKIP'
            'SKIP'
            'SKIP'
            'SKIP'
            'SKIP'
            'SKIP')

package() {
    # 1. 安裝應用程式主要 Py 檔到 /usr/share/
    install -d "${pkgdir}/usr/share/${pkgname}"
    install -m755 "${srcdir}/main.py" "${pkgdir}/usr/share/${pkgname}/main.py"
    install -m644 "${srcdir}/search.py" "${pkgdir}/usr/share/${pkgname}/search.py"
    install -m755 "${srcdir}/askpass.py" "${pkgdir}/usr/share/${pkgname}/askpass.py"

    # 2. 安裝命令列封裝器到 /usr/bin/
    install -d "${pkgdir}/usr/bin"
    install -m755 "${srcdir}/arch-app-installer" "${pkgdir}/usr/bin/arch-app-installer"

    # 3. 安裝系統桌面捷徑到 /usr/share/applications/
    install -d "${pkgdir}/usr/share/applications"
    install -m644 "${srcdir}/org.rendy.arch.appinstaller.desktop" "${pkgdir}/usr/share/applications/org.rendy.arch.appinstaller.desktop"

    # 4. 安裝系統級 Dolphin 右鍵選單服務選單 (適用於所有使用者)
    install -d "${pkgdir}/usr/share/kio/servicemenus"
    install -m644 "${srcdir}/arch-app-installer-file.desktop" "${pkgdir}/usr/share/kio/servicemenus/arch-app-installer-file.desktop"
    install -m644 "${srcdir}/arch-app-installer-folder.desktop" "${pkgdir}/usr/share/kio/servicemenus/arch-app-installer-folder.desktop"
}
