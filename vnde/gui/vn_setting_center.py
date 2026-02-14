#!/usr/bin/env python3
import shutil
import subprocess

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #0a5c36, #8f1118); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #ffffff; }
.hero-sub { color: #ffffff; font-weight: 700; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.title { font-size: 18px; font-weight: 800; color: #ffffff; }
.desc { color: #ffffff; font-weight: 700; }
"""

ACTIONS = [
    ("Man hinh", "Cai dat display", "gnome-control-center display"),
    ("Mang", "Quan ly Wi-Fi va Ethernet", "gnome-control-center network"),
    ("Am thanh", "Cai dat loa va micro", "gnome-control-center sound"),
    ("Ban phim", "Bo go va phim tat", "gnome-control-center keyboard"),
    ("Nguoi dung", "Tai khoan va quyen truy cap", "gnome-control-center user-accounts"),
    ("Ung dung mac dinh", "Cai dat app mac dinh", "gnome-control-center default-apps"),
    ("Cap nhat he thong", "Chay cap nhat apt nhanh", "vn-terminal -e 'sudo apt update && sudo apt upgrade -y'"),
    ("Khoi dong lai giao dien", "Restart GNOME Shell (X11)", "vn-terminal -e 'busctl --user call org.gnome.Shell /org/gnome/Shell org.gnome.Shell Eval s \"global.reexec_self()\"'"),
]


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNSetting(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.setting")

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN SETTING")
        win.set_icon_name("vnde-setting")
        win.set_default_size(1240, 820)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN SETTING", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Trung tam cai dat nhanh cho VNDE", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for name, desc, cmd in ACTIONS:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(360, 180)

            ttl = Gtk.Label(label=name, xalign=0)
            ttl.add_css_class("title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("desc")
            d.set_wrap(True)

            b = Gtk.Button(label="Mo")
            b.add_css_class("suggested-action")
            b.connect("clicked", self.on_open, cmd)

            card.append(ttl)
            card.append(d)
            card.append(b)
            flow.insert(card, -1)

        if not shutil.which("gnome-control-center"):
            warn = Gtk.Label(
                label="Khong tim thay gnome-control-center. Cai dat goi nay de dung day du tinh nang.",
                xalign=0,
            )
            warn.add_css_class("desc")
            root.append(warn)

        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_child(flow)

        root.append(hero)
        root.append(sc)
        win.set_child(root)
        win.maximize()
        win.present()

    def on_open(self, _btn, cmd):
        subprocess.Popen(["sh", "-lc", cmd])


if __name__ == "__main__":
    GLib.set_prgname("vnde-setting")
    VNSetting().run()
