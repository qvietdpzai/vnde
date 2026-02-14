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
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 10px; }
.list-pane { background: #11161d; border: 1px solid #2d3442; border-radius: 12px; }
.leftlist row { margin: 4px; border-radius: 10px; }
.leftlist row:selected { background: #1f354a; }
.status { color: #cfd6e2; }
.news-title { font-size: 17px; font-weight: 700; }
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
        self.win.set_default_size(1320, 860)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN News", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Tin tuc cap nhat theo RSS, de doc va gon gang", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.source = Gtk.DropDown.new_from_strings(list(FEEDS.keys()))
        self.source.connect("notify::selected", self.reload)
        self.search = Gtk.SearchEntry(placeholder_text="Tim tieu de bai viet...")
        self.search.connect("search-changed", self.render)
        btn = Gtk.Button(label="Lam moi")
        btn.add_css_class("suggested-action")
        btn.connect("clicked", self.reload)
        self.status = Gtk.Label(label="San sang", xalign=1)
        self.status.add_css_class("status")
        top.append(self.source)
        top.append(self.search)
        top.append(btn)
        top.append(self.status)

        body = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("leftlist")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self.on_select)

        left_sc = Gtk.ScrolledWindow()
        left_sc.set_min_content_width(520)
        left_sc.set_child(self.listbox)
        left_wrap = Gtk.Box()
        left_wrap.add_css_class("list-pane")
        left_wrap.append(left_sc)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right.add_css_class("card")

        self.detail_title = Gtk.Label(label="Chon bai viet", xalign=0)
        self.detail_title.add_css_class("news-title")
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

        body.set_start_child(left_wrap)
        body.set_end_child(right)
        body.set_resize_start_child(True)

        root.append(hero)
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
            for e in feed.entries[:100]:
                entries.append(
                    {
                        "title": unescape(getattr(e, "title", "(Khong tieu de)")),
                        "summary": unescape(getattr(e, "summary", "")),
                        "link": getattr(e, "link", ""),
                    }
                )
            GLib.idle_add(self.load_entries, src, entries)

        threading.Thread(target=worker, daemon=True).start()

    def load_entries(self, src, entries):
        self.items = entries
        self.render()
        now = datetime.datetime.now().strftime("%H:%M")
        self.set_status(f"{src}: {len(entries)} tin | cap nhat {now}")

    def render(self, *_args):
        term = self.search.get_text().strip().lower() if hasattr(self, "search") else ""

        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

        for item in self.items:
            if term and term not in item["title"].lower():
                continue
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(10)
            box.set_margin_end(10)

            title = Gtk.Label(label=item["title"], xalign=0)
            title.set_wrap(True)
            title.add_css_class("news-title")

            summary = Gtk.Label(label=(item["summary"] or "").replace("\n", " ")[:140], xalign=0)
            summary.set_wrap(True)
            summary.add_css_class("dim-label")

            box.append(title)
            box.append(summary)
            row.set_child(box)
            row._vnde_item = item
            self.listbox.append(row)

    def on_select(self, _lb, row):
        if row is None or not hasattr(row, "_vnde_item"):
            return
        item = row._vnde_item
        self.detail_title.set_label(item["title"])
        self.detail_text.set_label(item["summary"] or "(Khong co tom tat)")
        self.open_btn.set_sensitive(bool(item.get("link")))

    def open_link(self, _btn):
        row = self.listbox.get_selected_row()
        if row is None or not hasattr(row, "_vnde_item"):
            return
        link = row._vnde_item.get("link")
        if link:
            webbrowser.open(link)


if __name__ == "__main__":
    VNNews().run()
