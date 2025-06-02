import flet as ft
from backend import XrayBackend
import threading
import os
from collections import deque
import time
import checkver
import json
import logging
import string
import random
from const  import PROXY_IP , PROXY_PORT

class XrayClientUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.backend = XrayBackend()
        self.page.title = "XC (Xray-Client)"
        self.page.theme_mode = self.read_settinng("theme")
        self.debug_mod = self.read_settinng("debug")
        self.theme_color = self.change_theme_color(self.read_settinng("theme_color"))
        self.backend.log_callback = self.log
        self.page.padding = 20 # padding of all page
        self.page.window.min_width = 600
        self.page.window.min_height = 800
        self.useragent = self.read_settinng("useragent")
        self.current_view = "logs"  # Track current view: "logs" or "traffic"
        self.traffic_update_timer = None

        def handle_window_event(e):
            if e.data == "close":
                self.page.open(confirm_dialog)
        self.page.window.prevent_close = True
        self.page.window.on_event = handle_window_event

        self.selected_config = None
        self.selected_profile = None
        self.real_delay_stat = None
        self.ping_all_button = None
        self.close_event = self.backend.close_event
        self.cancel_real_delay_stat = "0"
        self.ping_type = self.read_settinng("ping")
        self.run_mode = "proxy"
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[ft.Tab(text="Home")],
            expand=1,
        )
        self.last_update_time = 0
        self.update_interval = 0.5
        self.log_buffer = deque(maxlen=30)
        self.pending_updates = []
        self.update_timer = None
        self.last_logged_message = None

        def yes_click(e):
            if self.backend.xray_process is None:
                self.page.window.destroy()
                return
            self.toggle_xray(e="1")
            self.page.window.destroy()
        def no_click(e):
            self.page.close(confirm_dialog)
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm"),
            content=ft.Text("Do you really want to exit XC ?"),
            actions=[
                ft.ElevatedButton("Yes", on_click=yes_click),
                ft.OutlinedButton("No", on_click=no_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.create_ui()
    
    @staticmethod
    def read_settinng (type) :
        default_settings = {
            "ping": "Tcping", 
            "theme": "dark",
            "theme_color": "blue",
            "debug": "off",
            "useragent": "XC(Xray-Client)"
        }
        if os.path.exists("./setting.json"):
            with open("./setting.json", "r") as file:
                f = file.read()
                if f.strip():
                    try:
                        data = json.loads(f)
                        ping = data.get("ping", default_settings["ping"])
                        theme = data.get("theme", default_settings["theme"])
                        theme_color = data.get("theme_color" , default_settings["theme_color"])
                        debug = data.get("debug", default_settings["debug"])
                        useragent = data.get("useragent", default_settings["useragent"])
                    except json.JSONDecodeError:

                        print("Error decoding JSON, using default settings.")
                        ping = default_settings["ping"]
                        theme = default_settings["theme"]
                        theme_color = default_settings["theme_color"]
                        debug = default_settings["debug"]
                        useragent = default_settings["useragent"]
                else:

                    print("File is empty, using default settings.")
                    ping = default_settings["ping"]
                    theme = default_settings["theme"]
                    theme_color = default_settings["theme_color"]
                    debug = default_settings["debug"]
                    useragent = default_settings["useragent"]
                    with open("./setting.json" , "w") as file :
                        data = json.dumps(default_settings , indent=4)
                        file.write(data)
        else:
            print("File not found, using default settings.")
            ping = default_settings["ping"]
            theme = default_settings["theme"]
            theme_color = default_settings["theme_color"]
            debug = default_settings["debug"]
            useragent = default_settings["useragent"]
            with open("./setting.json" , "w") as file :
                data = json.dumps(default_settings , indent=4)
                file.write(data)
        if type == "ping" :
            return ping
        elif type == "theme" :
            theme_mode = data.get("theme", default_settings["theme"])
            if theme_mode == "dark" :
                return ft.ThemeMode.DARK
            elif theme_mode == "light" :
                return ft.ThemeMode.LIGHT
        elif type == "theme_color":
            return theme_color
        elif type == "debug" :
            return debug
        elif type == "useragent" :
            return useragent

    def write_setting(self , type , value):
        default_settings = {
            "ping": "Tcping", 
            "theme": "dark",
            "theme_color": "blue",
            "debug": "off",
            "useragent": "XC(Xray-Client)"
        }
        if os.path.exists("./setting.json"):
            with open("./setting.json", "r") as file:
                f = file.read()
                
                if f.strip():
                    try:
                        data = json.loads(f)
                    except json.JSONDecodeError:
                        print("Error decoding JSON, using default settings.")
                        data = default_settings
                else:
                    print("File is empty, using default settings.")
                    data = default_settings
        else:
            print("File not found, using default settings.")
            data = default_settings

        if type == "ping":
            data["ping"] = value
        elif type == "theme":
            data["theme"] = value
        elif type == "debug" :
            data["debug"] = value
        elif type ==  "useragent" :
            data["useragent"] = value
        elif type == "theme_color":
            data["theme_color"] = value

        with open("./setting.json", "w") as file:
            json_data = json.dumps(data, indent=4)
            file.write(json_data)

    def check_for_updates(self):
        def run_update_check():
            checkver.main(self.page)
        threading.Thread(target=run_update_check, daemon=True).start()


    def create_ui(self):
        threading.Thread(target=self.check_for_close_signal, daemon=True).start()

        system_info = self.backend.get_system_info()

        settings_icon = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_size=28,
            on_click=self.show_settings_dialog,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK,
                bgcolor=ft.Colors.TRANSPARENT,
            ),
            tooltip="Settings",
        )

        import_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD_DOWNLOAD, size=20),
                    ft.Text("Import Subscription", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
                    ft.ControlState.HOVERED: ft.Colors.SECONDARY,
                },
            ),
            on_click=self.show_import_dialog,
        )

        header = ft.Row(
            controls=[import_button, ft.Container(expand=1), settings_icon],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.BOLT, size=30, color=ft.Colors.BLUE),
                        ft.Text("XC (Xray-Client)", size=28, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Text(f"XC Version: {self.backend.version}", size=16),
                            ft.Container(width=20),
                            ft.Text(f"Xray Version: {self.backend.xray_version}", size=16),
                        ] + ([
                            ft.ElevatedButton(
                                text="Install",
                                on_click=lambda _: self.check_for_updates()
                            )
                        ] if self.backend.xray_version == "Not Found" else []),
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=30, thickness=2),
                    *[
                        ft.Text(f"{key}: {value}", size=14, weight=ft.FontWeight.W_500)
                        for key, value in system_info.items()
                    ],
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=30,
                border_radius=10,
            ),
            elevation=8,
        )




        self.xray_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW),
                    ft.Text("Start", size=16, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.GREEN,
                    ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                },
            ),
            on_click=self.toggle_xray,
        )

        self.mode_switch = ft.Switch(
            label="Proxy",
            value=True,
            active_color=ft.Colors.GREY_400,
            inactive_thumb_color=ft.Colors.PRIMARY,
            on_change=self.toggle_mode,
        )

        self.log_view = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
            min_lines=12,
            max_lines=20,
            border_color=ft.Colors.SECONDARY,
            border_radius=8,
            text_size=14,
            visible=True,  # Initially visible
        )

        self.traffic_view = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.UPLOAD, color=ft.Colors.GREEN),
                            ft.Text("Upload: 0 B/s", size=16, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        expand=True,
                        margin=5,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE),
                            ft.Text("Download: 0 B/s", size=16, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        expand=True,
                        margin=5,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DATA_USAGE, color=ft.Colors.ORANGE),
                            ft.Text("Total Upload: 0 B", size=16, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        expand=True,
                        margin=5,
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DATA_USAGE, color=ft.Colors.PURPLE),
                            ft.Text("Total Download: 0 B", size=16, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        expand=True,
                        margin=5,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            # spacing=5
            ),
            # padding=10,
            expand=True,
            visible=False,  # Initially hidden
        )

        view_switch = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SWAP_HORIZ),
                    ft.Text("Switch View", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self.toggle_view,
        )
        
        home_content = ft.Column([
            info_card,
            ft.Container(height=20),
            ft.Row([
                self.xray_button,
                ft.Container(width=20),
                self.mode_switch,
                ft.Container(width=20),
                view_switch,
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=5),
            ft.Row([
                ft.Icon(ft.Icons.TERMINAL, color=ft.Colors.PRIMARY),
                ft.Text("Xray Status:", size=18, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.log_view,
            self.traffic_view,
        ], expand=True, spacing=15)

        self.tabs.tabs[0].content = home_content

        for profile in self.backend.get_profiles():
            self.add_profile_tab(profile)

        self.page.add(header, self.tabs)
        self.log("XC - Created By wikm , 3ircle with ❤️")
        self.check_for_updates()


    def add_profile_tab(self, profile):
        configs = self.backend.get_configs(profile)
        config_list = ft.ListView(expand=1, spacing=0, padding=20)

        # Create search field
        search_field = ft.TextField(
            label="Search configs",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=lambda e, lst=config_list, p=profile: self.filter_configs(e.control.value, lst, p),
            height=40,
            text_size=14,
            content_padding=10,
        )

        for config in configs:
            config_list.controls.append(self.create_config_tile_with_ping(config, profile))

        update_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.REFRESH, size=20),
                    ft.Text("Update", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self.update_subscription(profile)
        )

        delete_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.DELETE, size=20),
                    ft.Text("Delete", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self.delete_subscription(profile)
        )

        edit_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT, size=20),
                    ft.Text("Edit", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self.show_edit_dialog(profile)
        )

        # create profile specific
        ping_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.NETWORK_CHECK, size=20),
                    ft.Text("Ping All", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            data={"profile": profile, "status": "0"},  # save status of button
            on_click=lambda e: self.ping_button(e.control, config_list)
        )

        # Replace sort button with dropdown button
        sort_button = ft.PopupMenuButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SORT, size=20),
                    # ft.Text("Sort", size=16),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            items=[
                ft.PopupMenuItem(
                    text="By Ping",
                    icon=ft.Icons.NETWORK_PING,
                    on_click=lambda _: self.sort_configs_by_ping(config_list)
                ),
                ft.PopupMenuItem(
                    text="By Number",
                    icon=ft.Icons.FORMAT_LIST_NUMBERED,
                    on_click=lambda _: self.sort_configs_by_number(config_list)
                ),
            ],
            tooltip="Sort configs"
        )

        # Add search field to the tab content
        tab_content = ft.Column([
            ft.Row([update_button, delete_button, edit_button, ping_button, sort_button],
                alignment=ft.MainAxisAlignment.START,
                spacing=10),
            ft.Container(
                content=search_field,
                padding=ft.padding.symmetric(horizontal=20, vertical=10)
            ),
            config_list
        ], expand=True)

        self.tabs.tabs.append(ft.Tab(text=profile, content=tab_content))
        self.page.update()

        # check previous selected config
        try:
            with open(f"./core/{self.backend.os_sys}/select.txt", "r") as file:
                data = file.readlines()
                if data:
                    index = data[0].split("/")[3].split(".")[0]
                    p = data[0].split("/")[2]
                    print(index, p)

                    json_path = f"./subs/{p}/list.json"
                    if os.path.exists(json_path):
                        with open(json_path, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            self.selected_config = str(index) + " " + "-" + " " + data[index]
                            self.selected_profile = p
                        self.refresh_profile_tab(p)
                    else:
                        print(f"config NotFound : {json_path}")
        except :
            self.log("Core Not installed ...")


    def show_edit_dialog(self, profile):
        profile_path = f"./subs/{profile}"
        link_file_path = f"{profile_path}/url.txt"

        try:
            with open(link_file_path, "r") as f:
                current_link = f.read().strip()
        except FileNotFoundError:
            current_link = ""

        name_field = ft.TextField(value=profile, label="Profile Name", expand=True)
        link_field = ft.TextField(value=current_link, label="Subscription Link", expand=True)

        def save_changes(e):
            new_name = name_field.value.strip()
            new_link = link_field.value.strip()

            if new_name and new_link:
                if new_name != profile:
                    os.rename(profile_path, f"./subs/{new_name}")

                with open(f"./subs/{new_name}/url.txt", "w") as f:
                    f.write(new_link)

                for tab in self.tabs.tabs:
                    if tab.text == profile:
                        tab.text = new_name
                        break

                self.update_subscription(new_name)
                self.page.update()
                self.close_dialog(edit_dialog)

        edit_dialog = ft.AlertDialog(
            title=ft.Text("Edit Profile"),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_field,
                        link_field,
                    ],
                    spacing=20,
                ),
                padding=20,
                width=400,
            ),
            actions=[
                ft.TextButton("Save", on_click=save_changes),
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(edit_dialog)),
            ],
        )
        self.page.overlay.append(edit_dialog)
        edit_dialog.open = True
        self.page.update()


    def show_settings_dialog(self, e):
        ping_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Real-delay"),
                ft.dropdown.Option("Tcping"),
            ],
            value=self.ping_type,
            on_change=self.change_ping_type,
            expand=True,
        )
        theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Dark"),
                ft.dropdown.Option("Light"),
            ],
            value=self.page.theme_mode.name.capitalize(),
            on_change=self.change_theme,
            expand=True,
        )

        useragent_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("XC(Xray-Client)"),
                ft.dropdown.Option("v2rayNG/1.9.16"),
            ],
            value=self.useragent,
            on_change= self.change_useragent,
            expand=True
            )

        debug_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("on"),
                ft.dropdown.Option("off"),
            ],
            value=self.debug_mod,
            on_change=self.change_debug,
            expand=True,
        )

        theme_color_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("blue"),
                ft.dropdown.Option("red"),
                ft.dropdown.Option("green"),
                ft.dropdown.Option("purple"),
                ft.dropdown.Option("orange"),
            ],
            value=self.read_settinng("theme_color"),
            on_change=self.change_theme_color,
            expand=True,
        )

        github_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PUBLIC, size=20),
                    ft.Text("GitHub", size=16),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                shape=ft.RoundedRectangleBorder(radius=10),
                color=ft.Colors.WHITE,
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.BLUE,
                    ft.ControlState.HOVERED: ft.Colors.BLUE_700,
                },
            ),
            tooltip="Visit GitHub Repository",
            on_click=lambda _: self.open_github(),
        )


        settings_dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Text("Ping Type : "), ping_type_dropdown],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [ft.Text("Theme : "), theme_dropdown],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [ft.Text("Debug : "), debug_dropdown],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [ft.Text("User-Agent : "), useragent_dropdown],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [ft.Text("Theme Color : "), theme_color_dropdown],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=20, thickness=1),
                        ft.Row(
                            [github_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=20,
                ),
                padding=20,
                width=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.close_dialog(settings_dialog))
            ],
        )

        self.page.overlay.append(settings_dialog)
        settings_dialog.open = True
        self.page.update()


    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/wikm360/xray-client")



    def create_config_tile_with_ping(self, config, profile):
        is_selected = config == self.selected_config and profile == self.selected_profile
        def ping_selected_config(e):
            if self.ping_type == "Real-delay":
                self.xray_button.disabled = True
                self.xray_button.content = ft.Row (
                                [
                                    ft.Icon(ft.Icons.PLAY_ARROW),
                                    ft.Text("Start", size=16, weight=ft.FontWeight.W_500),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            )
                self.xray_button.style = ft.ButtonStyle(
                                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                                shape=ft.RoundedRectangleBorder(radius=10),
                                color={
                                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                                },
                                bgcolor={
                                    ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                    ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                                },
                            )
            config_num = config.split("-")[0].strip()
            result = self.backend.ping_config(profile, config_num, self.ping_type)
            e.control.trailing.content.value = f"Ping: {result}"
            self.xray_button.disabled = False
            self.page.update()

        return ft.ListTile(
            leading=ft.Icon(
                ft.Icons.CLOUD,
                color=ft.Colors.PRIMARY if is_selected else ft.Colors.GREY,
                size=24,
            ),
            title=ft.Container(
                content=ft.Text(
                    config,
                    size=16,
                    weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL,
                ),
                bgcolor=ft.Colors.TRANSPARENT,  # Remove background color from container
                padding=ft.padding.all(12),
                animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
                border_radius=8,
            ),
            trailing=ft.Container(
                content=ft.Text(
                    "Ping: -",
                    size=16,
                    color=ft.Colors.GREY_700,
                ),
                padding=ft.padding.all(8),
            ),
            selected=is_selected,
            on_click=lambda _, c=config, p=profile: self.select_config(c, p),
            on_long_press=ping_selected_config,
            tooltip="Hold to Ping",
            bgcolor=ft.Colors.SECONDARY if is_selected else ft.Colors.TRANSPARENT,  # Move background color to ListTile
        )

    # "0"  = cancel does not exist
    #  "1" = cancel showed
    #  "2" = camcel clicked   
    def ping_button(self, button, config_list):
        if button.data["status"] == "0":
            button.content.controls[1].value = "Cancel"
            button.data["status"] = "1"
            self.ping_all_configs(button.data["profile"], config_list, button)
        elif button.data["status"] == "1": 
            button.content.controls[1].value = "Ping All"
            button.data["status"] = "2"
        self.page.update()

    def ping_all_configs(self, profile, config_list, ping_button):
        if self.ping_type == "Real-delay":
            self.backend.stop_xray()
            self.xray_button.disabled = True
            self.xray_button.content = ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW),
                    ft.Text("Start", size=16, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
            self.xray_button.style = ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.GREEN,
                    ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                },
            )

        def ping_worker():
            try:
                configs = []
                for control in config_list.controls:
                    if isinstance(control, ft.ListTile):
                        configs.append({
                            'control': control,
                            'config_num': control.title.content.value.split("-")[0].strip()
                        })

                def process_config_batch(batch):
                    threads = []
                    results = {}

                    def ping_single_config(config):
                        if ping_button.data["status"] == "2":
                            return
                        
                        result = self.backend.ping_config(profile, config['config_num'], self.ping_type)
                        with threading.Lock():
                            results[config['control']] = result
                            # به‌روزرسانی UI برای هر نتیجه پینگ
                            # def update_result():
                            config['control'].trailing.content.value = f"Ping: {result}"
                            self.page.update()
                            # self.page.run_on_ui_thread(update_result)

                    for config in batch:
                        if ping_button.data["status"] == "2":
                            break
                        
                        thread = threading.Thread(
                            target=ping_single_config,
                            args=(config,),
                            daemon=True
                        )
                        threads.append(thread)
                        thread.start()

                    # Wait for all threads in batch to complete
                    for thread in threads:
                        thread.join(timeout=5)  # 5 second timeout

                # Process configs in batches of 5
                batch_size = 5
                for i in range(0, len(configs), batch_size):
                    if ping_button.data["status"] == "2":
                        break
                    
                    batch = configs[i:i + batch_size]
                    process_config_batch(batch)
                    time.sleep(0.1)  # Small delay between batches

            finally:
                # Ensure these operations run even if there's an error
                # def update_ui():
                ping_button.content.controls[1].value = "Ping All"
                ping_button.data["status"] = "0"
                self.xray_button.disabled = False
                
                if self.ping_type == "Real-delay" and self.backend.xray_process:
                    self.backend.stop_xray()
                
                self.page.update()
                    # self.schedule_update()

                # self.page.run_on_ui_thread(update_ui)

        threading.Thread(target=ping_worker, daemon=True).start()

    def select_config(self, config, profile):
        self.selected_config = config
        self.selected_profile = profile  # ذخیره نام پروفایل
        try:
            config_index = int(config.split("-")[0])
            with open(f"./core/{self.backend.os_sys}/select.txt", "w") as f:
                f.write(f"./subs/{profile}/{config_index}.json")
            self.log(f"Config {config_index} selected.")
        except Exception as e:
            self.log(f"Error selecting config: {str(e)}")
        self.refresh_profile_tab(profile)
        if self.backend.xray_process is None:
            pass
        else:
            self.toggle_xray(e="default")
            self.toggle_xray(e="default")

    def refresh_profile_tab(self , profile):
        if profile == "all" :
            self.selected_config = None
            self.selected_profile = None  # ریست کردن پروفایل انتخاب شده
            self.tabs.tabs = [tab for tab in self.tabs.tabs if tab.text == "Home"]

            for profile in self.backend.get_profiles():
                self.add_profile_tab(profile)
    
        else :
            for tab in self.tabs.tabs:
                if tab.text == profile:
                    configs = self.backend.get_configs(profile)
                    # Get the ListView which is the last control in tab content
                    config_list = tab.content.controls[2]  # Changed from [1] to [2] because of search field
                    
                    # Update existing configs' appearance
                    config_list.controls.clear()  # پاک کردن همه کانفیگ‌ها
                    for config in configs:  # اضافه کردن مجدد با وضعیت جدید
                        config_list.controls.append(self.create_config_tile_with_ping(config, profile))
                            
                    break
        self.page.update()

    def show_import_dialog(self, e):
        def import_sub(dialog):
            name = name_field.value
            url = url_field.value
            
            if name and url:
                loading_dialog.open = True
                self.page.update()
                
                def process_import():
                    try:
                        self.backend.import_subscription(name, url)
                        self.add_profile_tab(name)
                        self.page.open(ft.SnackBar(ft.Text("Subscription imported successfully!"), open=True))
                    except Exception as error:
                        self.page.open(ft.SnackBar(ft.Text(f"Error: {error}"), open=True))
                    finally:
                        loading_dialog.open = False
                        dialog.open = False
                        self.page.update()
                        self.refresh_profile_tab("all")

                # Run backend import in a separate thread
                threading.Thread(target=process_import).start()

        def load_json_file(picker_result):
            if picker_result.files:
                file_path = picker_result.files[0].path
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = file.read()
                        letters = string.ascii_letters
                        random_word = ''.join(random.choice(letters) for _ in range(8))
                        self.backend.import_subscription(random_word, data)
                        dialog.open = False
                        self.page.open(ft.SnackBar(ft.Text("JSON file imported successfully!"), open=True))
                        self.page.update()
                        self.refresh_profile_tab("all")

                except Exception as ex:
                    self.page.open(ft.SnackBar(ft.Text(f"Error loading JSON file: {ex}"), open=True))

        # Input fields for subscription
        name_field = ft.TextField(label="Profile Name")
        url_field = ft.TextField(label="URL")

        # FilePicker for JSON selection
        file_picker = ft.FilePicker(on_result=load_json_file)

        # Loading dialog
        loading_dialog = ft.AlertDialog(
            title=ft.Text("Loading"),
            content=ft.ProgressBar(),
            modal=True,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Import Subscription"),
            content=ft.Column(
                [
                    name_field,
                    url_field,
                    ft.TextButton(
                        "Load JSON File",
                        on_click=lambda _: file_picker.pick_files(
                            allow_multiple=False, file_type="application/json"
                        ),
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                ft.TextButton("Import", on_click=lambda _: import_sub(dialog)),
            ],
        )

        # Add FilePicker and dialogs to page overlay
        self.page.overlay.extend([file_picker, loading_dialog, dialog])

        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def run_with_sudo(self, password):
        config_path = f"./core/{self.backend.os_sys}/select.txt"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                selected_config = f.read().strip()
            message = self.backend.run(selected_config, "tun", sudo_password=password)
            self.log(message)
            if "Successfully" in message:
                self.xray_button.content = ft.Row(
                    [
                        ft.Icon(ft.Icons.STOP),
                        ft.Text("Stop", size=16, weight=ft.FontWeight.W_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                )
                self.xray_button.style = ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.Colors.RED,
                        ft.ControlState.HOVERED: ft.Colors.RED_700,
                    }
                )
            self.page.update()
        else:
            self.log("No config selected. Please select a config first.")

    def toggle_mode(self, e):
        if e.control.value:
            self.run_mode = "proxy"
            e.control.label = "Proxy"
        else:
            self.run_mode = "tun"
            e.control.label = "TUN"
        self.page.update()

    def toggle_xray(self, e):
        if self.backend.xray_process is None:
            config_path = f"./core/{self.backend.os_sys}/select.txt"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    selected_config = f.read().strip()
                if not selected_config:
                    self.log("first select one config...")
                    return
                if self.run_mode == "tun":
                    if self.backend.os_sys == "linux":
                        self.show_sudo_password_dialog(selected_config)
                    else:
                        message = self.backend.run(selected_config, "tun")
                        self.handle_xray_start(message)
                else:
                    message = self.backend.run(selected_config, "proxy")
                    self.handle_xray_start(message)
                    # اضافه کردن: روشن کردن پروکسی سیستم در حالت پروکسی
                    if self.run_mode == "proxy":
                        if self.backend.os_sys == "win":
                            self.backend.set_system_proxy(PROXY_IP, PROXY_PORT)
                        elif self.backend.os_sys == "linux":
                            self.backend.set_gnome_proxy(PROXY_IP, PROXY_PORT)
            else:
                self.log("No config selected. Please select a config first.")
        else:
            message = self.backend.stop_xray()
            self.xray_button.content = ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW),
                    ft.Text("Start", size=16, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
            self.xray_button.style = ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.GREEN,
                    ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                },
            )
            self.log(message)
            # اضافه کردن: خاموش کردن پروکسی سیستم در حالت پروکسی
            if self.run_mode == "proxy":
                if self.backend.os_sys == "win":
                    self.backend.disable_system_proxy()
                elif self.backend.os_sys == "linux":
                    self.backend.disable_gnome_proxy()
        self.page.update()

    def handle_xray_start(self, message):
        self.log(message)
        if "Successfully" in message or "Xray started successfully" in message:
            self.xray_button.content = ft.Row(
                [
                    ft.Icon(ft.Icons.STOP),
                    ft.Text("Stop", size=16, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
            self.xray_button.style = ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.RED,
                    ft.ControlState.HOVERED: ft.Colors.RED_700,
                }
            )

    def show_sudo_password_dialog(self , selected_config):
        def submit_password(e):
            password = password_field.value
            dialog.open = False
            self.page.update()
            message = self.backend.run(selected_config, "tun", sudo_password=password)
            self.handle_xray_start(message)

        password_field = ft.TextField(
            label="Enter sudo password",
            password=True,
            on_submit=submit_password
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Sudo Authentication"),
            content=ft.Column([
                ft.Text("This operation requires root privileges."),
                password_field
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                ft.TextButton("Submit", on_click=submit_password),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def read_xray_logs(self):
        for log_line in self.backend.read_xray_logs():
            self.log(log_line)

    def change_debug(self , e) :
        selected_debug = e.control.value
        if selected_debug == "on":
            self.debug_mod = "on"
            self.write_setting("debug" , "on")
        elif selected_debug == "off":
            self.debug_mod = "off"
            self.write_setting("debug" , "off")

    def change_theme(self, e):
        selected_theme = e.control.value
        if selected_theme == "Dark":
            self.page.theme_mode = ft.ThemeMode.DARK
            self.write_setting("theme" , "dark")
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.write_setting("theme" , "light")
        self.page.update()
        self.refresh_profile_tab(profile="all")
        print(f"Theme changed to: {selected_theme}")

    def change_useragent(self, event) :
        self.useragent = event.control.value
        self.write_setting("useragent" , self.useragent)

    def change_ping_type(self, e):
        selected_ping_type = e.control.value
        if selected_ping_type == "Real-delay":
            self.ping_type = "Real-delay"
            self.write_setting("ping" , "Real-delay")
        else:
            self.ping_type = "Tcping"
            self.write_setting("ping" , "Tcping")
        print(f"Ping type changed to: {self.ping_type}")

    def change_theme_color(self, e):
        color = getattr(e, "control", None)
        if color:
            color = color.value
        else:
            color = e

        self.write_setting("theme_color", color)
        
        # تنظیم رنگ‌های مختلف برنامه
        if color == "blue":
            primary_color = ft.Colors.BLUE
            primary_container = ft.Colors.BLUE_100
            secondary_color = ft.Colors.BLUE_700
        elif color == "red":
            primary_color = ft.Colors.RED
            primary_container = ft.Colors.RED_100
            secondary_color = ft.Colors.RED_700
        elif color == "green":
            primary_color = ft.Colors.GREEN
            primary_container = ft.Colors.GREEN_100
            secondary_color = ft.Colors.GREEN_700
        elif color == "purple":
            primary_color = ft.Colors.PURPLE
            primary_container = ft.Colors.PURPLE_100
            secondary_color = ft.Colors.PURPLE_700
        elif color == "orange":
            primary_color = ft.Colors.ORANGE
            primary_container = ft.Colors.ORANGE_100
            secondary_color = ft.Colors.ORANGE_700

        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=primary_color,
                primary_container=primary_container,
                secondary=secondary_color
            )
        )
        self.page.update()

    def log(self, message):
        if message is None or not isinstance(message, str):
            return

        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        if message != self.last_logged_message:
            self.log_buffer.append(message)
            
            # فقط 500 کاراکتر آخر نمایش داده شود
            log_text = "\n".join(filter(None, self.log_buffer))
            if len(log_text) > 500:
                log_text = log_text[-500:]
            
            self.log_view.value = log_text
            
            self.pending_updates.append("log")
            self.schedule_update()
            
            self.last_update_time = current_time
            self.last_logged_message = message
            
            if self.debug_mod == "on":
                logging.debug(message)

    def batch_update(self):
        """انجام به‌روزرسانی‌های تجمیع شده"""
        if self.pending_updates and not self.page.window.minimized:
        # if self.pending_updates :
            self.page.update()
            self.pending_updates.clear()
        self.update_timer = None

    def schedule_update(self):
        """زمان‌بندی به‌روزرسانی با تاخیر"""
        if not self.update_timer:
            self.update_timer = threading.Timer(0.1, self.batch_update)
            self.update_timer.start()

    def update_subscription(self, profile):
        loading_dialog = ft.AlertDialog(
            title=ft.Text("Updating..."),
            content=ft.ProgressBar(),
            modal=True
        )

        self.page.overlay.append(loading_dialog)
        loading_dialog.open = True
        self.page.update()

        def process_update():
            try:
                self.backend.update_subscription(profile)
                self.refresh_profile_tab(profile="all")
                self.page.open(ft.SnackBar(
                    ft.Text("Subscription updated successfully!"),
                    open=True
                ))
            except Exception as error:
                self.page.open(ft.SnackBar(
                    ft.Text(f"Update error: {error}"),
                    open=True
                ))
            finally:
                loading_dialog.open = False
                self.page.update()

        threading.Thread(target=process_update).start()

    def delete_subscription(self, profile):
        def confirm_delete(e):
            self.backend.delete_subscription(profile)
            self.tabs.tabs = [tab for tab in self.tabs.tabs if tab.text != profile]
            self.refresh_profile_tab(profile="all")
            self.close_dialog(confirm_dialog)

        def cancel_delete(e):
            self.close_dialog(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Delete Confirmation"),
            content=ft.Text(f"Are you sure you want to delete the profile '{profile}'?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()


    def check_for_close_signal(self):
        while True:
            if self.close_event.is_set():
                print("Closing UI as per backend request...")
                self.page.window_close()
                break
            time.sleep(0.1)

    def cleanup(self):
        """پاکسازی منابع هنگام بستن برنامه"""
        if self.update_timer:
            self.update_timer.cancel()
        if self.traffic_update_timer:
            self.traffic_update_timer.cancel()
        self.log_buffer.clear()
        self.pending_updates.clear()

    def sort_configs_by_ping(self, config_list):
        configs = []
        for control in config_list.controls:
            if isinstance(control, ft.ListTile):
                ping_text = control.trailing.content.value
                try:
                    # Extract ping value (assuming format "Ping: XXXms" or "Ping: -")
                    ping_value = ping_text.split(": ")[1]
                    if ping_value == "-":
                        ping = float('inf')  # Unpinged configs go to the end
                    else:
                        ping = float(ping_value.replace("ms", ""))
                except:
                    ping = float('inf')
                
                configs.append((ping, control))

        # Sort configs by ping value
        sorted_configs = sorted(configs, key=lambda x: x[0])
        
        # Update the ListView with sorted configs
        config_list.controls = [config[1] for config in sorted_configs]
        self.page.update()

    def sort_configs_by_number(self, config_list):
        """Sort configs by their number"""
        configs = []
        for control in config_list.controls:
            if isinstance(control, ft.ListTile):
                try:
                    # Extract config number from the title
                    config_num = int(control.title.content.value.split("-")[0].strip())
                    configs.append((config_num, control))
                except:
                    configs.append((float('inf'), control))
        
        # Sort configs by number
        sorted_configs = sorted(configs, key=lambda x: x[0])
        
        # Update the ListView with sorted configs
        config_list.controls = [config[1] for config in sorted_configs]
        self.page.update()

    def toggle_view(self, e):
        self.current_view = "traffic" if self.current_view == "logs" else "logs"
        self.log_view.visible = self.current_view == "logs"
        self.traffic_view.visible = self.current_view == "traffic"
        
        # Start or stop traffic updates based on view
        if self.current_view == "traffic":
            self.start_traffic_updates()
        else:
            self.stop_traffic_updates()
            
        self.page.update()

    def start_traffic_updates(self):
        def update_traffic():
            if self.traffic_view.visible and self.backend.xray_process:
                # دریافت آمار ترافیک از بکند
                stats = self.backend.get_traffic_stats()
                if stats:
                    upload_speed, download_speed = stats.get('speed', (0, 0))
                    total_upload, total_download = stats.get('total', (0, 0))
                    
                    # به‌روزرسانی نمایش ترافیک - اصلاح مسیر دسترسی به المان‌ها
                    row1_containers = self.traffic_view.content.controls[0].controls
                    row2_containers = self.traffic_view.content.controls[1].controls
                    
                    row1_containers[0].content.controls[1].value = f"Upload: {self.format_bytes(upload_speed)}/s"
                    row1_containers[1].content.controls[1].value = f"Download: {self.format_bytes(download_speed)}/s"
                    row2_containers[0].content.controls[1].value = f"Total Upload: {self.format_bytes(total_upload)}"
                    row2_containers[1].content.controls[1].value = f"Total Download: {self.format_bytes(total_download)}"
                    
                    self.page.update()

            # زمان‌بندی به‌روزرسانی بعدی
            if self.traffic_view.visible:
                self.traffic_update_timer = threading.Timer(1.0, update_traffic)
                self.traffic_update_timer.start()

        update_traffic()

    def stop_traffic_updates(self):
        if self.traffic_update_timer:
            self.traffic_update_timer.cancel()
            self.traffic_update_timer = None

    @staticmethod
    def format_bytes(bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
        return f"{bytes:.2f} TB"

    def filter_configs(self, search_text, config_list, profile):
        """Filter configs based on search text"""
        if not search_text:
            # If search text is empty, show all configs
            config_list.controls.clear()
            for config in self.backend.get_configs(profile):
                config_list.controls.append(self.create_config_tile_with_ping(config, profile))
        else:
            # Filter configs that contain the search text (case-insensitive)
            search_text = search_text.lower()
            config_list.controls.clear()
            for config in self.backend.get_configs(profile):
                if search_text in config.lower():
                    config_list.controls.append(self.create_config_tile_with_ping(config, profile))
        
        self.page.update()

def main(page: ft.Page):
    XrayClientUI(page)

if __name__ == "__main__":
    try:
        if XrayClientUI.read_settinng("debug") == "on" :
            logging.basicConfig(filename='xc_debug.log', level=logging.DEBUG)
            logging.debug("Starting application...")
        
        ft.app(target=main)
    except Exception as e:
        logging.error(f"Error starting application: {str(e)}")
        with open('error.log', 'w') as f:
            f.write(str(e))