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

class XrayClientUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.backend = XrayBackend()
        self.page.title = "XC (Xray-Client)"
        self.page.theme_mode = self.read_settinng("theme")
        self.debug_mod = self.read_settinng("debug")
        self.backend.log_callback = self.log
        self.page.padding = 20 # padding of all page
        self.page.window.min_width = 600
        self.page.window.min_height =730
        self.useragent = self.read_settinng("useragent")

        def handle_window_event(e):
            if e.data == "close":
                self.page.open(confirm_dialog)
        self.page.window.prevent_close = True
        self.page.window.on_event = handle_window_event

        self.selected_config = None
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
        self.log_buffer = deque(maxlen=100)
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
        default_settings = {"ping": "Tcping", "theme": "dark" , "debug":"off" , "useragent" : "XC(Xray-Client)"}
        if os.path.exists("./setting.json"):
            with open("./setting.json", "r") as file:
                f = file.read()
                if f.strip():
                    try:
                        data = json.loads(f)
                        ping = data.get("ping", default_settings["ping"])
                        theme = data.get("theme", default_settings["theme"])
                        debug = data.get("debug", default_settings["debug"])
                        useragent = data.get("useragent", default_settings["useragent"])
                    except json.JSONDecodeError:

                        print("Error decoding JSON, using default settings.")
                        ping = default_settings["ping"]
                        theme = default_settings["theme"]
                        debug = default_settings["debug"]
                        useragent = default_settings["useragent"]
                else:

                    print("File is empty, using default settings.")
                    ping = default_settings["ping"]
                    theme = default_settings["theme"]
                    debug = default_settings["debug"]
                    useragent = default_settings["useragent"]
                    with open("./setting.json" , "w") as file :
                        data = json.dumps(default_settings , indent=4)
                        file.write(data)
        else:
            print("File not found, using default settings.")
            ping = default_settings["ping"]
            theme = default_settings["theme"]
            debug = default_settings["debug"]
            useragent = default_settings["useragent"]
            with open("./setting.json" , "w") as file :
                data = json.dumps(default_settings , indent=4)
                file.write(data)
        if type == "ping" :
            return ping
        elif type == "theme" :
            if theme == "dark" :
                return ft.ThemeMode.DARK
            elif theme == "light" :
                return ft.ThemeMode.LIGHT
        elif type == "debug" :
            return debug
        elif type == "useragent" :
            return useragent

    def write_setting(self , type , value):
        default_settings = {"ping": "Tcping", "theme": "dark" , "debug":"off" , "useragent" : "XC(Xray-Client)"}
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
                    ft.ControlState.DEFAULT: ft.Colors.BLUE,
                    ft.ControlState.HOVERED: ft.Colors.BLUE_700,
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
                    ft.Row([
                        ft.Text(f"XC Version: {self.backend.version}", size=16),
                        ft.Container(width=20),
                        ft.Text(f"Xray Version: {self.backend.xray_version}", size=16),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(height=30, thickness=2),
                    *[ft.Text(f"{key}: {value}", size=14, weight=ft.FontWeight.W_500) 
                      for key, value in system_info.items()],
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
            inactive_thumb_color=ft.Colors.BLUE,
            on_change=self.toggle_mode,
        )

        self.log_view = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
            min_lines=12,
            max_lines=20,
            border_color=ft.Colors.BLUE_200,
            border_radius=8,
            text_size=14,
        )
        
        home_content = ft.Column([
            info_card,
            ft.Container(height=20),
            ft.Row([
                self.xray_button,
                ft.Container(width=20),
                self.mode_switch
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=5),
            ft.Row([
                ft.Icon(ft.Icons.TERMINAL, color=ft.Colors.BLUE),
                ft.Text("Xray Logs:", size=18, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.log_view
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

        tab_content = ft.Column([
            ft.Row([update_button, delete_button, edit_button, ping_button],
                alignment=ft.MainAxisAlignment.START,
                spacing=10), 
            config_list
        ], expand=True)

        self.tabs.tabs.append(ft.Tab(text=profile, content=tab_content))
        self.page.update()

        # check previous selected config
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
                    self.refresh_profile_tab(p)
                else:
                    print(f"config NotFound : {json_path}")


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
        is_selected = config == self.selected_config
        
        return ft.ListTile(
            leading=ft.Icon(
                ft.Icons.CLOUD,
                color=ft.Colors.BLUE if is_selected else ft.Colors.GREY,
                size=24,
            ),
            title=ft.Container(
                content=ft.Text(
                    config,
                    size=16,
                    weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL
                ),
                bgcolor=ft.Colors.BLUE_100 if is_selected else ft.Colors.TRANSPARENT,
                padding=ft.padding.all(12),
                animate=ft.animation.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
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

        def ping_worker():
            for control in config_list.controls:
                if isinstance(control, ft.ListTile):
                    config_name = control.title.content.value
                    ping_text = control.trailing.content
                    config_num = config_name.split("-")[0].strip()
                    result = self.backend.ping_config(profile, config_num, self.ping_type)

                    if ping_button.data["status"] == "2":
                        self.xray_button.disabled = False
                        break

                    ping_text.value = f"Ping: {result}"
                    self.page.update()

            ping_button.content.controls[1].value = "Ping All"
            ping_button.data["status"] = "0"
            self.xray_button.disabled = False
            self.page.update()

        threading.Thread(target=ping_worker, daemon=True).start()

    def select_config(self, config, profile):
        self.selected_config = config
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
        else :
            self.toggle_xray(e="default")
            self.toggle_xray(e="default")

    def refresh_profile_tab(self , profile):
        if profile == "all" :
            self.selected_config = None
            self.tabs.tabs = [tab for tab in self.tabs.tabs if tab.text == "Home"]

            for profile in self.backend.get_profiles():
                self.add_profile_tab(profile)
    
        else :
            for tab in self.tabs.tabs:
                if tab.text == profile:
                    configs = self.backend.get_configs(profile)
                    config_list = tab.content.controls[1]
                    for control in config_list.controls:
                        config_name = control.title.content.value
                        if config_name == self.selected_config:
                            control.title.content.bgcolor = ft.Colors.LIGHT_BLUE
                        else:
                            control.title.content.bgcolor = ft.Colors.TRANSPARENT
                    for config in configs:
                        if not any(control.title.content.value == config for control in config_list.controls):
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
                        self.page.snack_bar = ft.SnackBar(ft.Text("Subscription imported successfully!"), open=True)
                    except Exception as error:
                        self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {error}"), open=True)
                    finally:
                        loading_dialog.open = False
                        dialog.open = False
                        self.page.update()

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
                        self.refresh_profile_tab("all")
                        dialog.open = False
                        self.page.snack_bar = ft.SnackBar(ft.Text("JSON file imported successfully!"), open=True)
                        self.page.update()

                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Error loading JSON file: {ex}"), open=True)

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
                if not selected_config :
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
            else:
                self.log("No config selected. Please select a config first.")
        else:
            message = self.backend.stop_xray()
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
            self.log(message)
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

    def log(self, message):
        if message is not None:
            self.log_buffer.append(str(message))
        else:
            self.log_buffer.append("None")
        self.log_view.value = "\n".join(filter(None, self.log_buffer))
        self.page.update()

        if message != self.last_logged_message:
            logging.debug(message)
            self.last_logged_message = message
        
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
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Subscription updated successfully!"),
                    open=True
                )
            except Exception as error:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Update error: {error}"),
                    open=True
                )
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