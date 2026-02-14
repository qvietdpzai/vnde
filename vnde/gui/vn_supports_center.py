#!/usr/bin/env python3
import webbrowser

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #ffffff; }
.hero-sub { color: #ffffff; font-weight: 700; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.title { font-size: 18px; font-weight: 800; color: #ffffff; }
.body-text { color: #ffffff; font-weight: 700; }
"""

SUPPORTS = [
    ("Github VNDE", "Noi bao loi va dong gop cho du an", "https://github.com/qvietdpzai/vnde"),
    ("Telegram Support", "Kenh trao doi cong dong", "https://t.me"),
    ("Email Support", "Gui email ho tro tructiep", "mailto:support@vnde.local"),
    ("Huong dan su dung", "Xem tai lieu README", "https://github.com/qvietdpzai/vnde#readme"),
]


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNSupports(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.supports")

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN SUPPORTS")
        win.set_default_size(1200, 780)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN SUPPORTS", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Lien he va nhan ho tro cho VNDE", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(2)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for name, desc, url in SUPPORTS:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")
            card.set_size_request(460, 190)

            title = Gtk.Label(label=name, xalign=0)
            title.add_css_class("title")
            d = Gtk.Label(label=desc, xalign=0)
            d.add_css_class("body-text")
            d.set_wrap(True)
            u = Gtk.Label(label=url, xalign=0)
            u.add_css_class("body-text")
            u.set_wrap(True)

            btn = Gtk.Button(label="Mo")
            btn.add_css_class("suggested-action")
            btn.connect("clicked", lambda _b, link=url: webbrowser.open(link))

            card.append(title)
            card.append(d)
            card.append(u)
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
    VNSupports().run()
