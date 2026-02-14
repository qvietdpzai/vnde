#!/usr/bin/env python3
import json
import os
import time
import uuid

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

DATA_PATH = os.path.expanduser("~/.local/share/vnde/forum_posts.json")
PEERS_PATH = os.path.expanduser("~/.local/share/vnde/forum_peers.json")

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #ffffff; }
.hero-sub { color: #ffffff; font-weight: 700; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.title { font-size: 18px; font-weight: 800; color: #ffffff; }
.meta { color: #ffffff; font-weight: 700; }
"""


def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_posts():
    ensure_data_file()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts):
    ensure_data_file()
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNForum(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.forum")
        self.posts = []

    def do_activate(self):
        apply_css()
        self.posts = load_posts()

        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN FORUM")
        win.set_icon_name("vnde-forum")
        win.set_default_size(1280, 840)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        title = Gtk.Label(label="VN FORUM", xalign=0)
        title.add_css_class("hero-title")
        sub = Gtk.Label(label="Dien dan noi bo VNDE: dang bai, thao luan, chia se kinh nghiem", xalign=0)
        sub.add_css_class("hero-sub")
        hero.append(title)
        hero.append(sub)
        self.peer_label = Gtk.Label(label="Peers online: 0", xalign=0)
        self.peer_label.add_css_class("hero-sub")
        hero.append(self.peer_label)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        form.add_css_class("card")
        self.input_title = Gtk.Entry(placeholder_text="Tieu de bai viet...")
        self.input_body = Gtk.TextView()
        self.input_body.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.input_body.set_size_request(-1, 110)
        post_btn = Gtk.Button(label="Dang bai")
        post_btn.add_css_class("suggested-action")
        post_btn.connect("clicked", self.on_post)
        form.append(self.input_title)
        form.append(self.input_body)
        form.append(post_btn)

        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_min_children_per_line(1)
        self.flow.set_max_children_per_line(2)
        self.flow.set_column_spacing(12)
        self.flow.set_row_spacing(12)

        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_child(self.flow)

        root.append(hero)
        root.append(form)
        root.append(sc)
        win.set_child(root)
        self.render_posts()
        GLib.timeout_add_seconds(4, self.refresh_state)
        win.maximize()
        win.present()

    def on_post(self, _btn):
        t = self.input_title.get_text().strip()
        buf = self.input_body.get_buffer()
        btxt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()
        if not t or not btxt:
            return
        self.posts.insert(
            0,
            {
                "id": str(uuid.uuid4()),
                "title": t,
                "body": btxt,
                "author": os.environ.get("USER", "user"),
                "created": time.strftime("%d/%m/%Y %H:%M"),
                "created_ts": int(time.time()),
                "origin": os.uname().nodename,
            },
        )
        save_posts(self.posts)
        self.input_title.set_text("")
        buf.set_text("")
        self.render_posts()

    def render_posts(self):
        child = self.flow.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.flow.remove(child)
            child = nxt

        for p in self.posts:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("card")
            card.set_size_request(560, 210)

            t = Gtk.Label(label=p.get("title", ""), xalign=0)
            t.add_css_class("title")
            m = Gtk.Label(label=f"{p.get('author','user')} | {p.get('created','')}", xalign=0)
            m.add_css_class("meta")
            b = Gtk.Label(label=p.get("body", ""), xalign=0)
            b.add_css_class("meta")
            b.set_wrap(True)
            b.set_selectable(True)

            card.append(t)
            card.append(m)
            card.append(b)
            self.flow.insert(card, -1)

    def refresh_state(self):
        self.posts = load_posts()
        self.render_posts()
        peers = {}
        try:
            if os.path.exists(PEERS_PATH):
                with open(PEERS_PATH, "r", encoding="utf-8") as f:
                    peers = json.load(f)
        except Exception:
            peers = {}
        self.peer_label.set_label(f"Peers online: {len(peers)}")
        return True


if __name__ == "__main__":
    GLib.set_prgname("vnde-forum")
    VNForum().run()
