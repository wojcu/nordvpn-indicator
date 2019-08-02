import gi  # noqa
gi.require_version("Gtk", "3.0")  # noqa
gi.require_version("AppIndicator3", "0.1")  # noqa
from gi.repository import Gtk as gtk  # noqa
from gi.repository import AppIndicator3 as appindicator  # noqa
from gi.repository import GLib as glib  # noqa
import subprocess


class Connection:
    def __init__(self):
        self.status = False
        self.data = {}


def do_connect(_):
    subprocess.run(["nordvpn", "connect"], check=True)


def do_disconnect(_):
    subprocess.run(["nordvpn", "disconnect"], check=True)


def do_quit(_):
    gtk.main_quit()


class Menu:
    def __init__(self, connection):
        self.connection = connection
        self.menu = gtk.Menu()
        if self.connection.status:
            self.toggle_button = gtk.MenuItem.new_with_label("Disconnect")
            self.toggle_handle = self.toggle_button.connect(
                "activate", do_disconnect)
        else:
            self.toggle_button = gtk.MenuItem.new_with_label("Connect")
            self.toggle_handle = self.toggle_button.connect(
                "activate", do_connect)
        self.menu.append(self.toggle_button)
        self.info_buttons = {}
        for k, v in self.connection.data.items():
            info_button = gtk.MenuItem.new_with_label(f"{k}: {v}")
            info_button.set_sensitive(False)
            self.info_buttons[k] = info_button
            self.menu.insert(info_button, 1)
        self.exit_item = gtk.MenuItem.new()
        self.exit_item.set_label("Exit")
        self.exit_item.connect("activate", do_quit)
        self.menu.append(self.exit_item)
        self.menu.show_all()

    def gtk_handle(self):
        return self.menu

    def update(self, connection):
        if connection.status != self.connection.status:
            self.toggle_button.disconnect(self.toggle_handle)
            if connection.status:
                self.toggle_button.set_label("Disconnect")
                self.toggle_handle = self.toggle_button.connect(
                    "activate", do_disconnect)
            else:
                self.toggle_button.set_label("Connect")
                self.toggle_handle = self.toggle_button.connect(
                    "activate", do_connect)
        expired = {}
        for k, v in self.info_buttons.items():
            if k not in connection.data:
                expired[k] = v
        for k,v in expired.items():
            self.menu.remove(v)
            del self.info_buttons[k]
        for k, v in connection.data.items():
            if k not in self.info_buttons:
                info_button = gtk.MenuItem.new_with_label(f"{k}: {v}")
                info_button.set_sensitive(False)
                self.info_buttons[k] = info_button
                self.menu.insert(info_button, 1)
            else:
                self.info_buttons[k].set_label(f"{k}: {v}")
        self.menu.show_all()
        self.connection = connection


def connection_info():
    out = subprocess.run(["nordvpn", "status"],
                         capture_output=True, check=True)
    stdout = out.stdout.decode("utf8")
    lines = stdout.split("\n")
    connection = Connection()
    for line in lines:
        tokens = line.split(": ")
        if len(tokens) != 2:
            continue
        head, value = tokens
        if head == "Status":
            if value == "Connected":
                connection.status = True
            else:
                connection.status = False
        else:
            connection.data[head] = value
    return connection


def icon_for_status(status):
    if status:
        return "nordvpn", "NordVPN connected"
    else:
        return "nordvpn_red", "NordVPN disconnected"


def do_update_status(indicator, menu):
    con = connection_info()
    icon = icon_for_status(con.status)
    indicator.set_icon_full(*icon)
    menu.update(con)
    return glib.SOURCE_CONTINUE


def main():
    connection = connection_info()
    icon, _ = icon_for_status(connection.status)
    indicator_id = "nordvpn"
    category = appindicator.IndicatorCategory.APPLICATION_STATUS
    indicator = appindicator.Indicator.new(indicator_id, icon, category)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    menu = Menu(connection)
    indicator.set_menu(menu.gtk_handle())
    glib.timeout_add(1000, do_update_status, indicator, menu)
    gtk.main()


if __name__ == "__main__":
    main()
