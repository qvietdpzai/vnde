#!/usr/bin/env python3
import subprocess
import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

CSS = """
window { background: #0f1115; }
.hero { background: linear-gradient(110deg, #8f1118, #0a5c36); border-radius: 14px; padding: 14px; }
.hero-title { font-size: 24px; font-weight: 800; color: #ffffff; }
.hero-sub { color: #ffffff; font-weight: 700; }
.card { background: #1b1f27; border: 1px solid #2d3442; border-radius: 14px; padding: 12px; }
.title { font-size: 18px; font-weight: 800; color: #ffffff; }
.val { color: #ffffff; font-weight: 700; }
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def cpu_percent():
    with open("/proc/stat", "r", encoding="utf-8") as f:
        first = f.readline().split()[1:]
    vals1 = list(map(int, first))
    total1 = sum(vals1)
    idle1 = vals1[3]
    time.sleep(0.15)
    with open("/proc/stat", "r", encoding="utf-8") as f:
        second = f.readline().split()[1:]
    vals2 = list(map(int, second))
    total2 = sum(vals2)
    idle2 = vals2[3]
    dt = max(total2 - total1, 1)
    didle = idle2 - idle1
    return round((1 - didle / dt) * 100, 1)


def mem_percent():
    data = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            k, v = line.split(":", 1)
            data[k.strip()] = int(v.strip().split()[0])
    total = data.get("MemTotal", 1)
    avail = data.get("MemAvailable", 0)
    used = total - avail
    return round(used * 100 / total, 1)


def disk_percent():
    out = subprocess.check_output(["sh", "-lc", "df -h / | awk 'NR==2{print $5}'"], text=True).strip()
    return out or "N/A"


def top_processes():
    cmd = "ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 9"
    return subprocess.check_output(["sh", "-lc", cmd], text=True).strip()


class VNMonitor(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="vn.de.monitor")

    def do_activate(self):
        apply_css()
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("VN MONITOR")
        self.win.set_icon_name("vnde-monitor")
        self.win.set_default_size(1240, 820)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(14)
        root.set_margin_bottom(14)
        root.set_margin_start(14)
        root.set_margin_end(14)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("hero")
        t = Gtk.Label(label="VN MONITOR", xalign=0)
        t.add_css_class("hero-title")
        s = Gtk.Label(label="Theo doi tai nguyen he thong thoi gian thuc", xalign=0)
        s.add_css_class("hero-sub")
        hero.append(t)
        hero.append(s)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.cpu = Gtk.Label(label="CPU: ...", xalign=0)
        self.cpu.add_css_class("val")
        self.ram = Gtk.Label(label="RAM: ...", xalign=0)
        self.ram.add_css_class("val")
        self.disk = Gtk.Label(label="Disk: ...", xalign=0)
        self.disk.add_css_class("val")
        row.append(self.cpu)
        row.append(self.ram)
        row.append(self.disk)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("card")
        ttl = Gtk.Label(label="Top process theo CPU", xalign=0)
        ttl.add_css_class("title")
        self.proc = Gtk.TextView()
        self.proc.set_editable(False)
        self.proc.set_cursor_visible(False)
        self.proc.set_monospace(True)
        self.proc.set_wrap_mode(Gtk.WrapMode.NONE)
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_child(self.proc)
        card.append(ttl)
        card.append(sc)

        root.append(hero)
        root.append(row)
        root.append(card)
        self.win.set_child(root)
        self.refresh()
        GLib.timeout_add_seconds(2, self.refresh)
        self.win.maximize()
        self.win.present()

    def refresh(self):
        try:
            self.cpu.set_label(f"CPU: {cpu_percent()}%")
            self.ram.set_label(f"RAM: {mem_percent()}%")
            self.disk.set_label(f"Disk: {disk_percent()}")
            txt = top_processes()
            self.proc.get_buffer().set_text(txt)
        except Exception as e:
            self.proc.get_buffer().set_text(f"Loi monitor: {e}")
        return True


if __name__ == "__main__":
    GLib.set_prgname("vnde-monitor")
    VNMonitor().run()
