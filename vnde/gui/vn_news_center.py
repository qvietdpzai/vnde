#!/usr/bin/env python3
import datetime
import threading
import webbrowser
from html import unescape

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

try:
    import feedparser
except Exception:
    feedparser = None

FEEDS = {
    "VnExpress": "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "Tuoi Tre": "https://tuoitre.vn/rss/tin-moi-nhat.rss",
    "Thanh Nien": "https://thanhnien.vn/rss/home.rss",
    "Dan Tri": "https://dantri.com.vn/rss/home.rss",
}

CSS = """
window { background: #111315; }
.big-title { font-size: 20px; font-weight: 800; }
.card { background: #1f2328; border: 1px solid #2d333b; border-radius: 14px; padding: 8px; }
.leftlist row { margin: 4px; border-radius: 10px; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class VNNews(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.news")
        self.items = []

    def do_activate(self):
        apply_css()
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("VN News")
        self.win.maximize()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label(label="VN News", xalign=0)
        title.add_css_class("big-title")
        self.source = Gtk.DropDown.new_from_strings(list(FEEDS.keys()))
        self.source.connect("notify::selected", self.reload)
        btn = Gtk.Button(label="Lam moi")
        btn.add_css_class("suggested-action")
        btn.connect("clicked", self.reload)
        self.status = Gtk.Label(label="San sang", xalign=1)
        self.status.add_css_class("dim-label")
        top.append(title)
        top.append(self.source)
        top.append(btn)
        top.append(self.status)

        body = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("leftlist")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self.on_select)
        left_sc = Gtk.ScrolledWindow()
        left_sc.set_min_content_width(480)
        left_sc.set_child(self.listbox)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right.add_css_class("card")
        self.detail_title = Gtk.Label(label="Chon bai viet", xalign=0)
        self.detail_title.add_css_class("title-3")
        self.detail_title.set_wrap(True)
        self.detail_text = Gtk.Label(label="", xalign=0)
        self.detail_text.set_wrap(True)
        self.detail_text.set_selectable(True)
        detail_sc = Gtk.ScrolledWindow()
        detail_sc.set_child(self.detail_text)
        self.open_btn = Gtk.Button(label="Mo bai goc")
        self.open_btn.add_css_class("suggested-action")
        self.open_btn.set_sensitive(False)
        self.open_btn.connect("clicked", self.open_link)
        right.append(self.detail_title)
        right.append(detail_sc)
        right.append(self.open_btn)

        body.set_start_child(left_sc)
        body.set_end_child(right)
        body.set_resize_start_child(True)

        root.append(top)
        root.append(body)
        self.win.set_child(root)
        self.win.present()
        self.reload()

    def set_status(self, text):
        self.status.set_label(text)

    def reload(self, *_args):
        if feedparser is None:
            self.set_status("Thieu python3-feedparser")
            return
        src = self.source.get_selected_item().get_string()
        url = FEEDS[src]
        self.set_status(f"Dang tai {src}...")

        def worker():
            feed = feedparser.parse(url)
            entries = []
            for e in feed.entries[:80]:
                entries.append({
                    "title": unescape(getattr(e, "title", "(Khong tieu de)")),
                    "summary": unescape(getattr(e, "summary", "")),
                    "link": getattr(e, "link", ""),
                })
            GLib.idle_add(self.load_entries, src, entries)

        threading.Thread(target=worker, daemon=True).start()

    def load_entries(self, src, entries):
        self.items = entries
        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

        for item in entries:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(10)
            box.set_margin_end(10)
            t = Gtk.Label(label=item["title"], xalign=0)
            t.set_wrap(True)
            box.append(t)
            row.set_child(box)
            self.listbox.append(row)

        self.set_status(f"{src}: {len(entries)} tin | {datetime.datetime.now().strftime('%H:%M')}")

    def on_select(self, _lb, row):
        if row is None:
            return
        idx = row.get_index()
        if not (0 <= idx < len(self.items)):
            return
        item = self.items[idx]
        self.detail_title.set_label(item["title"])
        self.detail_text.set_label(item["summary"] or "(Khong co tom tat)")
        self.open_btn.set_sensitive(bool(item.get("link")))

    def open_link(self, _btn):
        row = self.listbox.get_selected_row()
        if row is None:
            return
        idx = row.get_index()
        if not (0 <= idx < len(self.items)):
            return
        link = self.items[idx].get("link")
        if link:
            webbrowser.open(link)


if __name__ == "__main__":
    VNNews().run()
