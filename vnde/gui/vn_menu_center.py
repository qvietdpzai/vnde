#!/usr/bin/env python3
import subprocess

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

MENU_ITEMS = [
    ("He thong", "VN App Center", "Mo kho ung dung VNDE", "vn-app-store"),
    ("He thong", "VN Terminal", "Terminal phong cach VNDE", "vn-terminal"),
    ("Tin tuc", "VN News", "Doc tin trong giao dien GUI", "vn-news"),
    ("Tin tuc", "VN News CLI", "Doc tin nhanh trong terminal", "vn-terminal -e vn-news-cli"),
    ("Giai tri", "VN Music", "Mo trung tam am nhac", "vn-music"),
    ("He thong", "Docker", "Mo trang thai docker", "vnde-docker.desktop"),
    ("He thong", "Settings", "Mo cai dat GNOME", "gnome-control-center"),
    ("Ung dung", "Firefox", "Trinh duyet web", "firefox"),
    ("Ung dung", "Files", "Quan ly file", "nautilus"),
]

CSS = """
window { background: #111315; }
.card { background: #1f2328; border-radius: 14px; border: 1px solid #2d333b; padding: 10px; }
.big-title { font-size: 20px; font-weight: 800; }
.menu-title { font-size: 16px; font-weight: 700; }
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
        self.win.maximize()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label(label="VN Menu", xalign=0)
        title.add_css_class("big-title")
        self.search = Gtk.SearchEntry(placeholder_text="Tim ung dung, chuc nang...")
        self.search.connect("search-changed", self.render)
        top.append(title)
        top.append(self.search)

        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_min_children_per_line(2)
        self.flow.set_max_children_per_line(4)
        self.flow.set_column_spacing(12)
        self.flow.set_row_spacing(12)

        sc = Gtk.ScrolledWindow()
        sc.set_child(self.flow)

        root.append(top)
        root.append(sc)
        self.win.set_child(root)
        self.render()
        self.win.present()

    def render(self, *_args):
        term = self.search.get_text().strip().lower()
        child = self.flow.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.flow.remove(child)
            child = nxt

        for group, name, desc, cmd in MENU_ITEMS:
            blob = f"{group} {name} {desc}".lower()
            if term and term not in blob:
                continue

            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("card")
            card.set_size_request(320, 150)

            t = Gtk.Label(label=f"[{group}] {name}", xalign=0)
            t.add_css_class("menu-title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("dim-label")
            d.set_wrap(True)
            b = Gtk.Button(label="Mo")
            b.add_css_class("suggested-action")
            b.connect("clicked", self.on_open, cmd)

            card.append(t)
            card.append(d)
            card.append(b)
            self.flow.insert(card, -1)

    def on_open(self, _btn, cmd):
        if cmd.endswith(".desktop"):
            subprocess.Popen(["gtk-launch", cmd])
            return
        subprocess.Popen(["sh", "-lc", cmd])


if __name__ == "__main__":
    VNMenu().run()
