#!/usr/bin/env python3
import subprocess

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

MENU_ITEMS = [
    ("He thong", "VN App Center", "Kho ung dung dep cua VNDE", "vn-app-store", "vnde-app-store"),
    ("He thong", "VN Terminal", "Terminal phong cach VNDE", "vn-terminal", "vnde-terminal"),
    ("He thong", "VN HELPER", "Tro giup thao tac nhanh cho he thong", "vn-helper", "vnde-helper"),
    ("He thong", "VN SUPPORTS", "Lien he va ho tro VNDE", "vn-supports", "vnde-supports"),
    ("He thong", "VN SETTING", "Trung tam cai dat cua VNDE", "vn-setting", "vnde-setting"),
    ("He thong", "VN MONITOR", "Theo doi tai nguyen he thong", "vn-monitor", "vnde-monitor"),
    ("He thong", "VN FORUM", "Dien dan noi bo cua cong dong VNDE", "vn-forum", "vnde-forum"),
    ("Tin tuc", "VN News", "Doc tin trong giao dien GUI", "vn-news", "vnde-news"),
    ("Tin tuc", "VN News CLI", "Doc tin nhanh trong terminal", "vn-terminal -e vn-news-cli", "vnde-news"),
    ("Giai tri", "VN Music", "Mo trung tam am nhac", "vn-music", "vnde-music"),
    ("He thong", "Docker", "Mo trang thai docker", "vnde-docker.desktop", "vnde-docker"),
    ("He thong", "Settings", "Cai dat he thong GNOME", "gnome-control-center", "preferences-system"),
    ("Ung dung", "Firefox", "Trinh duyet web", "firefox", "firefox"),
    ("Ung dung", "VN File Manager", "Quan ly file theo phong cach VNDE", "vn-file-manager", "vnde-file-manager"),
]

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border-radius: 14px; border: 1px solid #2d3442; padding: 12px; }
.menu-title { font-size: 17px; font-weight: 700; }
.group { color: #8fb4ff; font-weight: 700; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNMenu(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.menu")

    def do_activate(self):
        apply_css()
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("VN Menu")
        self.win.set_icon_name("vnde-menu")
        self.win.set_default_size(1280, 840)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN Menu", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Tat ca cong cu VNDE trong mot noi", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        self.search = Gtk.SearchEntry(placeholder_text="Tim ung dung, vi du: nhac, tin tuc, terminal...")
        self.search.connect("search-changed", self.render)

        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_min_children_per_line(2)
        self.flow.set_max_children_per_line(4)
        self.flow.set_column_spacing(12)
        self.flow.set_row_spacing(12)

        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_child(self.flow)

        root.append(hero)
        root.append(self.search)
        root.append(sc)
        self.win.set_child(root)

        self.render()
        self.win.maximize()
        self.win.present()

    def render(self, *_args):
        term = self.search.get_text().strip().lower()

        child = self.flow.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.flow.remove(child)
            child = nxt

        for group, name, desc, cmd, icon_name in MENU_ITEMS:
            blob = f"{group} {name} {desc}".lower()
            if term and term not in blob:
                continue

            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(320, 190)

            g = Gtk.Label(label=group, xalign=0)
            g.add_css_class("group")

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(30)
            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            t = Gtk.Label(label=name, xalign=0)
            t.add_css_class("menu-title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("dim-label")
            d.set_wrap(True)
            title_box.append(t)
            title_box.append(d)
            top.append(icon)
            top.append(title_box)

            b = Gtk.Button(label="Mo")
            b.add_css_class("suggested-action")
            b.connect("clicked", self.on_open, cmd)

            card.append(g)
            card.append(top)
            card.append(b)
            self.flow.insert(card, -1)

    def on_open(self, _btn, cmd):
        if cmd.endswith(".desktop"):
            subprocess.Popen(["gtk-launch", cmd])
            return
        subprocess.Popen(["sh", "-lc", cmd])


if __name__ == "__main__":
    GLib.set_prgname("vnde-menu")
    VNMenu().run()
