#!/usr/bin/env python3
import os
import subprocess

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #0a5c36, #8f1118); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border-radius: 14px; border: 1px solid #2d3442; padding: 12px; }
.title { font-size: 17px; font-weight: 700; }
"""

PLACES = [
    ("Home", os.path.expanduser("~"), "user-home"),
    ("Desktop", os.path.expanduser("~/Desktop"), "user-desktop"),
    ("Documents", os.path.expanduser("~/Documents"), "folder-documents"),
    ("Downloads", os.path.expanduser("~/Downloads"), "folder-download"),
    ("Pictures", os.path.expanduser("~/Pictures"), "folder-pictures"),
    ("Videos", os.path.expanduser("~/Videos"), "folder-videos"),
    ("Music", os.path.expanduser("~/Music"), "folder-music"),
    ("Filesystem", "/", "drive-harddisk"),
]


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def open_path(path):
    target = path if os.path.exists(path) else os.path.expanduser("~")
    if subprocess.call(["sh", "-lc", f"nautilus '{target}'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        subprocess.Popen(["xdg-open", target])


class VNFileManager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.filemanager")

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN File Manager")
        win.set_icon_name("vnde-file-manager")
        win.set_default_size(1180, 760)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN File Manager", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Mo nhanh thu muc pho bien va quan ly tep de dang", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(3)
        flow.set_max_children_per_line(4)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for name, path, icon_name in PLACES:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(250, 170)

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(30)
            ttl = Gtk.Label(label=name, xalign=0)
            ttl.add_css_class("title")
            top.append(icon)
            top.append(ttl)

            path_lbl = Gtk.Label(label=path, xalign=0)
            path_lbl.add_css_class("dim-label")
            path_lbl.set_wrap(True)

            btn = Gtk.Button(label="Mo")
            btn.add_css_class("suggested-action")
            btn.connect("clicked", lambda _b, p=path: open_path(p))

            card.append(top)
            card.append(path_lbl)
            card.append(btn)
            flow.insert(card, -1)

        open_default = Gtk.Button(label="Mo Nautilus Day Du")
        open_default.add_css_class("suggested-action")
        open_default.connect("clicked", lambda _b: open_path(os.path.expanduser("~")))

        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_child(flow)

        root.append(hero)
        root.append(open_default)
        root.append(sc)
        win.set_child(root)
        win.maximize()
        win.present()


if __name__ == "__main__":
    GLib.set_prgname("vnde-file-manager")
    VNFileManager().run()
