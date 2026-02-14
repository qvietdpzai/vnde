#!/usr/bin/env python3
import shutil
import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

APPS = [
    {"id": "firefox", "name": "Firefox", "desc": "Trinh duyet web", "native": "firefox", "launch": "firefox"},
    {"id": "chrome", "name": "Google Chrome", "desc": "Trinh duyet Google", "native": "google-chrome-stable", "launch": "google-chrome-stable"},
    {"id": "vlc", "name": "VLC", "desc": "Xem video va nghe nhac", "native": "vlc", "launch": "vlc"},
    {"id": "libreoffice", "name": "LibreOffice", "desc": "Bo ung dung van phong", "native": "libreoffice", "launch": "libreoffice"},
    {"id": "telegram", "name": "Telegram", "desc": "Nhan tin", "native": "telegram-desktop", "launch": "telegram-desktop"},
    {"id": "vscode", "name": "VS Code", "desc": "Lap trinh", "native": "code", "launch": "code"},
    {"id": "gimp", "name": "GIMP", "desc": "Sua anh", "native": "gimp", "launch": "gimp"},
    {"id": "obs", "name": "OBS Studio", "desc": "Quay man hinh", "native": "obs-studio", "launch": "obs"},
    {"id": "docker", "name": "Docker", "desc": "Nen tang container", "native": "docker.io", "launch": "vn-terminal -e 'docker ps'"},
]

CSS = """
window { background: #121212; }
.card { background: #1f1f1f; border-radius: 16px; border: 1px solid #2f2f2f; padding: 10px; }
.big-title { font-size: 20px; font-weight: 800; }
.app-title { font-size: 17px; font-weight: 700; }
.muted { color: #bbbbbb; }
.status { background: #1f2a1f; color: #d8ffd8; border-radius: 10px; padding: 8px 12px; }
.searchbox { border-radius: 12px; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def detect_pm():
    for pm in ("apt-get", "dnf", "pacman", "zypper"):
        if shutil.which(pm):
            return pm
    return ""


def install_cmd(app):
    pm = detect_pm()
    if pm == "apt-get":
        return f"apt-get update && apt-get install -y {app['native']}"
    if pm == "dnf":
        return f"dnf install -y {app['native']}"
    if pm == "pacman":
        return f"pacman -Sy --noconfirm {app['native']}"
    if pm == "zypper":
        return f"zypper install -y {app['native']}"
    return ""


def run_root(cmd):
    if shutil.which("pkexec"):
        return subprocess.run(["pkexec", "sh", "-lc", cmd], capture_output=True, text=True)
    return subprocess.run(["sh", "-lc", f"sudo {cmd}"], capture_output=True, text=True)


class Card(Gtk.Box):
    def __init__(self, app, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.app = app
        self.parent = parent
        self.add_css_class("card")
        self.set_size_request(340, 150)

        title = Gtk.Label(label=app["name"], xalign=0)
        title.add_css_class("app-title")
        desc = Gtk.Label(label=app["desc"], xalign=0)
        desc.add_css_class("muted")
        desc.set_wrap(True)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_install = Gtk.Button(label="Cai dat")
        btn_install.add_css_class("suggested-action")
        btn_install.connect("clicked", self.on_install)
        btn_open = Gtk.Button(label="Mo")
        btn_open.connect("clicked", self.on_open)
        actions.append(btn_install)
        actions.append(btn_open)

        self.append(title)
        self.append(desc)
        self.append(actions)

    def on_open(self, _btn):
        subprocess.Popen(["sh", "-lc", self.app["launch"]])

    def on_install(self, _btn):
        self.parent.install(self.app)


class VNAppCenter(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.appcenter")

    def do_activate(self):
        apply_css()
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("VN App Center")
        self.win.fullscreen()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title = Gtk.Label(label="VN App Center", xalign=0)
        title.add_css_class("big-title")
        self.search = Gtk.SearchEntry(placeholder_text="Tim app, vi du: browser, code, video...")
        self.search.add_css_class("searchbox")
        self.search.connect("search-changed", self.render)
        top.append(title)
        top.append(self.search)

        self.status = Gtk.Label(label="San sang", xalign=0)
        self.status.add_css_class("status")

        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_min_children_per_line(3)
        self.flow.set_max_children_per_line(5)
        self.flow.set_column_spacing(12)
        self.flow.set_row_spacing(12)

        sc = Gtk.ScrolledWindow()
        sc.set_child(self.flow)

        root.append(top)
        root.append(self.status)
        root.append(sc)
        self.win.set_child(root)

        self.render()
        self.win.present()

    def set_status(self, msg):
        self.status.set_label(msg)

    def render(self, *_):
        term = self.search.get_text().strip().lower()
        child = self.flow.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.flow.remove(child)
            child = next_child

        for app in APPS:
            blob = f"{app['id']} {app['name']} {app['desc']}".lower()
            if term and term not in blob:
                continue
            self.flow.insert(Card(app, self), -1)

    def install(self, app):
        cmd = install_cmd(app)
        if not cmd:
            self.set_status("Khong xac dinh duoc package manager")
            return
        self.set_status(f"Dang cai {app['name']}...")

        def worker():
            p = run_root(cmd)
            if p.returncode == 0:
                msg = f"Da cai {app['name']} thanh cong"
            else:
                msg = (p.stderr or p.stdout or "Cai dat that bai").strip().splitlines()[-1]
            GLib.idle_add(self.set_status, msg)

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    VNAppCenter().run()
