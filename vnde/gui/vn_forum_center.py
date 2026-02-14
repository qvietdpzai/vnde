#!/usr/bin/env python3
import base64
import json
import os
import shutil
import subprocess
import time
import uuid

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

DATA_PATH = os.path.expanduser("~/.local/share/vnde/forum_posts.json")
PEERS_PATH = os.path.expanduser("~/.local/share/vnde/forum_peers.json")
IMG_CACHE_DIR = os.path.expanduser("~/.cache/vnde/forum_images")

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
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_posts(posts):
    ensure_data_file()
    tmp = f"{DATA_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_PATH)


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
        self.selected_image_b64 = ""
        self.selected_image_name = ""
        self.last_posts_mtime = 0.0

    def do_activate(self):
        apply_css()
        self.posts = load_posts()

        win = Gtk.ApplicationWindow(application=self)
        self.win = win
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
        attach_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pick_img = Gtk.Button(label="Them anh")
        pick_img.connect("clicked", self.on_pick_image)
        self.image_info = Gtk.Label(label="Chua co anh", xalign=0)
        self.image_info.add_css_class("meta")
        attach_row.append(pick_img)
        attach_row.append(self.image_info)
        post_btn = Gtk.Button(label="Dang bai")
        post_btn.add_css_class("suggested-action")
        post_btn.connect("clicked", self.on_post)
        form.append(self.input_title)
        form.append(self.input_body)
        form.append(attach_row)
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
        if not t or (not btxt and not self.selected_image_b64):
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
                "image_b64": self.selected_image_b64,
                "image_name": self.selected_image_name,
                "reactions": {"like": 0, "love": 0, "haha": 0},
                "comments": [],
            },
        )
        save_posts(self.posts)
        self.input_title.set_text("")
        buf.set_text("")
        self.selected_image_b64 = ""
        self.selected_image_name = ""
        self.image_info.set_label("Chua co anh")
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
            card.set_size_request(560, -1)

            t = Gtk.Label(label=p.get("title", ""), xalign=0)
            t.add_css_class("title")
            m = Gtk.Label(label=f"{p.get('author','user')} | {p.get('created','')}", xalign=0)
            m.add_css_class("meta")
            b = Gtk.Label(label=p.get("body", ""), xalign=0)
            b.add_css_class("meta")
            b.set_wrap(True)
            b.set_selectable(True)

            img_widget = self.build_image_widget(p)
            reactions = self.build_reaction_bar(p)
            comments = self.build_comments_ui(p)

            card.append(t)
            card.append(m)
            card.append(b)
            if img_widget is not None:
                card.append(img_widget)
            card.append(reactions)
            card.append(comments)
            self.flow.insert(card, -1)

    def refresh_state(self):
        try:
            mtime = os.path.getmtime(DATA_PATH) if os.path.exists(DATA_PATH) else 0.0
            focused = self.get_active_window().get_focus() if self.get_active_window() else None
            typing_now = isinstance(focused, Gtk.Entry)
            if mtime != self.last_posts_mtime and not typing_now:
                self.posts = load_posts()
                self.render_posts()
                self.last_posts_mtime = mtime
        except Exception:
            pass
        peers = {}
        try:
            if os.path.exists(PEERS_PATH):
                with open(PEERS_PATH, "r", encoding="utf-8") as f:
                    peers = json.load(f)
        except Exception:
            peers = {}
        self.peer_label.set_label(f"Peers online: {len(peers)}")
        return True

    def on_pick_image(self, _btn):
        path = self.pick_image_path()
        if not path:
            return
        if not path or not os.path.isfile(path):
            return
        raw = b""
        with open(path, "rb") as fp:
            raw = fp.read()
        if len(raw) > 2 * 1024 * 1024:
            self.image_info.set_label("Anh qua lon (>2MB)")
            return
        self.selected_image_b64 = base64.b64encode(raw).decode("ascii")
        self.selected_image_name = os.path.basename(path)
        self.image_info.set_label(f"Da chon: {self.selected_image_name}")

    def pick_image_path(self):
        filters = "Anh | *.png *.jpg *.jpeg *.webp"
        try:
            if shutil.which("zenity"):
                p = subprocess.run(
                    [
                        "zenity",
                        "--file-selection",
                        "--title=Chon anh",
                        "--file-filter=*.png *.jpg *.jpeg *.webp",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if p.returncode == 0:
                    return p.stdout.strip()
                return ""
            if shutil.which("kdialog"):
                p = subprocess.run(
                    ["kdialog", "--getopenfilename", os.path.expanduser("~"), filters],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if p.returncode == 0:
                    return p.stdout.strip()
                return ""
        except Exception:
            return ""
        self.image_info.set_label("Thieu bo chon file (cai zenity hoac kdialog)")
        return ""

    def build_image_widget(self, post):
        b64 = post.get("image_b64", "")
        if not b64:
            return None
        try:
            os.makedirs(IMG_CACHE_DIR, exist_ok=True)
            out_path = os.path.join(IMG_CACHE_DIR, f"{post.get('id','img')}.bin")
            raw = base64.b64decode(b64)
            with open(out_path, "wb") as fp:
                fp.write(raw)
            loader = GdkPixbuf.PixbufLoader.new()
            loader.write(raw)
            loader.close()
            pix = loader.get_pixbuf()
            pic = Gtk.Picture.new_for_pixbuf(pix)
            pic.set_can_shrink(True)
            pic.set_size_request(520, 220)
            return pic
        except Exception:
            return None

    def build_reaction_bar(self, post):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        reacts = post.get("reactions", {})
        if not isinstance(reacts, dict):
            reacts = {"like": 0, "love": 0, "haha": 0}
        post["reactions"] = reacts

        defs = [
            ("like", "👍"),
            ("love", "❤️"),
            ("haha", "😂"),
        ]
        for key, emo in defs:
            count = int(reacts.get(key, 0))
            btn = Gtk.Button(label=f"{emo} {count}")
            btn.connect("clicked", self.on_react, post.get("id", ""), key)
            row.append(btn)
        return row

    def on_react(self, _btn, post_id, key):
        for p in self.posts:
            if p.get("id") != post_id:
                continue
            reacts = p.setdefault("reactions", {"like": 0, "love": 0, "haha": 0})
            reacts[key] = int(reacts.get(key, 0)) + 1
            break
        save_posts(self.posts)
        self.render_posts()

    def build_comments_ui(self, post):
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        comments = post.get("comments", [])
        if not isinstance(comments, list):
            comments = []
            post["comments"] = comments

        for c in comments[-4:]:
            txt = f"{c.get('author','user')}: {c.get('text','')}"
            lbl = Gtk.Label(label=txt, xalign=0)
            lbl.add_css_class("meta")
            lbl.set_wrap(True)
            wrap.append(lbl)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        entry = Gtk.Entry(placeholder_text="Viet binh luan...")
        send = Gtk.Button(label="Gui")
        send.add_css_class("suggested-action")
        send.connect("clicked", self.on_comment_send, post.get("id", ""), entry)
        row.append(entry)
        row.append(send)
        wrap.append(row)
        return wrap

    def on_comment_send(self, _btn, post_id, entry):
        text = entry.get_text().strip()
        if not text:
            return
        for p in self.posts:
            if p.get("id") != post_id:
                continue
            comments = p.setdefault("comments", [])
            comments.append(
                {
                    "author": os.environ.get("USER", "user"),
                    "text": text,
                    "created_ts": int(time.time()),
                }
            )
            break
        save_posts(self.posts)
        self.render_posts()


if __name__ == "__main__":
    GLib.set_prgname("vnde-forum")
    VNForum().run()
