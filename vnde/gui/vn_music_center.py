#!/usr/bin/env python3
import webbrowser

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

SERVICES = [
    ("Zing MP3", "Kho nhac Viet", "https://zingmp3.vn"),
    ("NhacCuaTui", "Nhac Viet de tim", "https://www.nhaccuatui.com"),
    ("YouTube Music", "Kho nhac quoc te", "https://music.youtube.com"),
    ("Spotify Web", "Playlist da nen", "https://open.spotify.com"),
]

CSS = """
window { background: #101214; }
.card { background: #1f2328; border: 1px solid #2d333b; border-radius: 14px; padding: 12px; }
.big-title { font-size: 20px; font-weight: 800; }
.svc-title { font-size: 17px; font-weight: 700; }
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
        win.fullscreen()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)

        title = Gtk.Label(label="VN Music", xalign=0)
        title.add_css_class("big-title")
        root.append(title)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for name, desc, url in SERVICES:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("card")
            card.set_size_request(340, 160)

            t = Gtk.Label(label=name, xalign=0)
            t.add_css_class("svc-title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("dim-label")
            d.set_wrap(True)
            btn = Gtk.Button(label="Mo dich vu")
            btn.add_css_class("suggested-action")
            btn.connect("clicked", lambda _b, u=url: webbrowser.open(u))

            card.append(t)
            card.append(d)
            card.append(btn)
            flow.insert(card, -1)

        sc = Gtk.ScrolledWindow()
        sc.set_child(flow)
        root.append(sc)

        win.set_child(root)
        win.present()


if __name__ == "__main__":
    VNMusic().run()
