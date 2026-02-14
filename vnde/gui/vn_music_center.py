#!/usr/bin/env python3
import webbrowser

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

SERVICES = [
    ("Zing MP3", "Kho nhac Viet", "https://zingmp3.vn", "multimedia-player"),
    ("NhacCuaTui", "Nhac Viet de tim", "https://www.nhaccuatui.com", "media-playback-start"),
    ("YouTube Music", "Kho nhac quoc te", "https://music.youtube.com", "applications-multimedia"),
    ("Spotify Web", "Playlist da nen", "https://open.spotify.com", "audio-x-generic"),
]

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #0a5c36, #8f1118); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.svc-title { font-size: 18px; font-weight: 700; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNMusic(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.music")

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN Music")
        win.set_icon_name("vnde-music")
        win.set_default_size(1280, 840)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN Music", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Truy cap nhanh cac dich vu nhac pho bien", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(14)
        flow.set_row_spacing(14)

        for name, desc, url, icon_name in SERVICES:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(360, 180)

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(34)
            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            t = Gtk.Label(label=name, xalign=0)
            t.add_css_class("svc-title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("dim-label")
            d.set_wrap(True)
            title_box.append(t)
            title_box.append(d)
            top.append(icon)
            top.append(title_box)

            btn = Gtk.Button(label="Mo dich vu")
            btn.add_css_class("suggested-action")
            btn.connect("clicked", lambda _b, u=url: webbrowser.open(u))

            card.append(top)
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


if __name__ == "__main__":
    GLib.set_prgname("vnde-music")
    VNMusic().run()
