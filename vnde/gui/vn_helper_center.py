#!/usr/bin/env python3
import subprocess

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #0a5c36, #8f1118); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.title { font-size: 18px; font-weight: 700; }
"""

HELP_ITEMS = [
    ("Cap nhat he thong", "sudo apt update && sudo apt upgrade -y"),
    ("Sua loi quyen file", "sudo chown -R $USER:$USER \"$HOME\""),
    ("Kiem tra mang", "ping -c 4 8.8.8.8"),
    ("Kiem tra dung luong", "df -h"),
    ("Kiem tra RAM", "free -h"),
]


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNHelper(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.helper")

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN HELPER")
        win.set_default_size(1200, 780)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN HELPER", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Cong cu tro giup nhanh cho nguoi dung VNDE", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for label, cmd in HELP_ITEMS:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(330, 180)

            title = Gtk.Label(label=label, xalign=0)
            title.add_css_class("title")

            cmd_lbl = Gtk.Label(label=cmd, xalign=0)
            cmd_lbl.add_css_class("dim-label")
            cmd_lbl.set_wrap(True)

            btn = Gtk.Button(label="Chay trong VN Terminal")
            btn.add_css_class("suggested-action")
            btn.connect("clicked", self.run_cmd, cmd)

            card.append(title)
            card.append(cmd_lbl)
            card.append(btn)
            flow.insert(card, -1)

        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_child(flow)

        root.append(hero)
        root.append(sc)
        win.set_child(root)
        win.maximize()
        win.present()

    def run_cmd(self, _btn, cmd):
        subprocess.Popen(["sh", "-lc", f"vn-terminal -e \"{cmd}\""])


if __name__ == "__main__":
    VNHelper().run()
