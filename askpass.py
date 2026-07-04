#!/usr/bin/env python3
import sys
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

class AskPassWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("需要授權")
        self.set_default_size(360, 180)
        self.set_resizable(False)
        
        # Save password output
        self.password = None
        
        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(18)
        vbox.set_margin_bottom(18)
        vbox.set_margin_start(18)
        vbox.set_margin_end(18)
        
        # Title and description
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>系統權限驗證</span>")
        title_label.set_halign(Gtk.Align.START)
        vbox.append(title_label)
        
        desc_label = Gtk.Label(label="執行安裝需要管理員權限，請輸入您的密碼：")
        desc_label.set_wrap(True)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("dim-label")
        vbox.append(desc_label)
        
        # Password entry field
        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)  # Hidden input
        self.entry.set_activates_default(True)  # Pressing Enter triggers suggested action
        self.entry.set_placeholder_text("密碼")
        vbox.append(self.entry)
        
        # Button box
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        
        btn_cancel = Gtk.Button(label="取消")
        btn_cancel.connect("clicked", self.on_cancel)
        btn_box.append(btn_cancel)
        
        btn_ok = Gtk.Button(label="確定")
        btn_ok.add_css_class("suggested-action")
        btn_ok.connect("clicked", self.on_ok)
        btn_box.append(btn_ok)
        
        vbox.append(btn_box)
        
        # Styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .dim-label {
                opacity: 0.7;
                font-size: 0.9rem;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.set_content(vbox)
        
    def on_ok(self, btn):
        self.password = self.entry.get_text()
        self.get_application().quit()
        
    def on_cancel(self, btn):
        self.password = None
        self.get_application().quit()

class AskPassApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.rendy.arch.appinstaller.askpass')
        self.password = None
        
    def do_activate(self):
        self.win = AskPassWindow(self)
        self.win.present()
        
    def get_password(self):
        return self.win.password if hasattr(self, 'win') else None

if __name__ == "__main__":
    app = AskPassApp()
    app.run([])
    pwd = app.get_password()
    if pwd is not None:
        print(pwd)
        sys.exit(0)
    else:
        sys.exit(1)
