#!/usr/bin/env python3
import shutil
import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fdf5d8; }
.hero-sub { color: #efe6c3; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 10px; }
.title { font-size: 16px; font-weight: 800; }
.muted { color: #b9bfca; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def run_bg(cmd: str):
    subprocess.Popen(["sh", "-lc", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class VNDocker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.docker")
        self.listbox = None
        self.status = None

    def do_activate(self):
        apply_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("VN Docker")
        win.set_icon_name("vnde-docker")
        win.set_default_size(1320, 860)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN Docker", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Quan ly container: start/stop/restart, logs va shell", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        refresh_btn = Gtk.Button(label="Lam moi")
        refresh_btn.connect("clicked", lambda _b: self.refresh())
        ps_btn = Gtk.Button(label="Mo docker ps")
        ps_btn.connect("clicked", lambda _b: run_bg("vn-terminal -e 'docker ps -a'"))
        install_btn = Gtk.Button(label="Cai Docker")
        install_btn.connect("clicked", lambda _b: run_bg("vn-terminal -e 'sudo apt update && sudo apt install -y docker.io docker-compose-v2'"))
        toolbar.append(refresh_btn)
        toolbar.append(ps_btn)
        toolbar.append(install_btn)

        self.status = Gtk.Label(label="San sang", xalign=0)
        self.status.add_css_class("muted")

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("boxed-list")
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_child(self.listbox)

        root.append(hero)
        root.append(toolbar)
        root.append(self.status)
        root.append(sc)
        win.set_child(root)
        win.maximize()
        win.present()
        self.refresh()

    def set_status(self, txt):
        GLib.idle_add(self.status.set_text, txt)

    def clear_list(self):
        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

    def add_row(self, name, image, state):
        row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        row_box.add_css_class("card")

        line1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label=name, xalign=0)
        title.add_css_class("title")
        title.set_hexpand(True)
        st = Gtk.Label(label=state, xalign=1)
        st.add_css_class("muted")
        line1.append(title)
        line1.append(st)

        info = Gtk.Label(label=image, xalign=0)
        info.add_css_class("muted")

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for label, cmd in (
            ("Start", f"docker start {name}"),
            ("Stop", f"docker stop {name}"),
            ("Restart", f"docker restart {name}"),
            ("Logs", f"vn-terminal -e 'docker logs -f {name}'"),
            ("Shell", f"vn-terminal -e 'docker exec -it {name} sh || docker exec -it {name} bash'"),
        ):
            b = Gtk.Button(label=label)
            b.connect("clicked", lambda _btn, c=cmd: self.run_action(c))
            actions.append(b)

        row_box.append(line1)
        row_box.append(info)
        row_box.append(actions)
        self.listbox.append(row_box)

    def run_action(self, cmd):
        run_bg(cmd)
        self.set_status(f"Da chay: {cmd}")
        GLib.timeout_add_seconds(2, lambda: (self.refresh(), False)[1])

    def refresh(self):
        self.set_status("Dang tai danh sach container...")
        self.clear_list()
        threading.Thread(target=self._load_containers, daemon=True).start()

    def _load_containers(self):
        if shutil.which("docker") is None:
            self.set_status("Chua co Docker. Bam 'Cai Docker' de cai.")
            return
        cmd = "docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}'"
        p = subprocess.run(["sh", "-lc", cmd], capture_output=True, text=True)
        if p.returncode != 0:
            self.set_status("Khong doc duoc Docker. Kiem tra quyen group docker.")
            return
        lines = [x.strip() for x in p.stdout.splitlines() if x.strip()]
        if not lines:
            self.set_status("Khong co container nao.")
            return
        for ln in lines:
            parts = ln.split("|", 2)
            if len(parts) != 3:
                continue
            name, image, state = parts
            GLib.idle_add(self.add_row, name, image, state)
        self.set_status(f"Da tai {len(lines)} container.")


if __name__ == "__main__":
    GLib.set_prgname("vnde-docker")
    VNDocker().run()
