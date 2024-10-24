import flet as ft
from backend import XrayBackend
import threading
import os
from collections import deque
import time
import checkver
import json
import logging

class XrayClientUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.backend = XrayBackend()
        self.page.title = "XC (Xray-Client)"
        self.page.theme_mode = self.read_settinng("theme")
        self.debug_mod = self.read_settinng("debug")
        self.backend.log_callback = self.log
        self.page.padding = 20
        self.selected_config = None
        self.real_delay_stat = None
        self.ping_all_button = None
        self.close_event = self.backend.close_event
        self.cancel_real_delay_stat = "0"
        self.ping_type = self.read_settinng("ping")
        self.run_mode = "proxy"  # Default mode
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[ft.Tab(text="Home")],
            expand=1,
        )
        self.log_buffer = deque(maxlen=1000)  # Limit log entries
        self.create_ui()
    
    @staticmethod
    def read_settinng (type) :
        default_settings = {"ping": "Tcping", "theme": "dark" , "debug":"off"}
        if os.path.exists("./setting.json"):
            with open("./setting.json", "r") as file:
                f = file.read()
                if f.strip():
                    try:
                        data = json.loads(f)
                        ping = data.get("ping", default_settings["ping"])
                        theme = data.get("theme", default_settings["theme"])
                        debug = data.get("debug", default_settings["debug"])
                    except json.JSONDecodeError:

                        print("Error decoding JSON, using default settings.")
                        ping = default_settings["ping"]
                        theme = default_settings["theme"]
                        debug = default_settings["debug"]
                else:

                    print("File is empty, using default settings.")
                    ping = default_settings["ping"]
                    theme = default_settings["theme"]
                    debug = default_settings["debug"]
                    with open("./setting.json" , "w") as file :
                        data = json.dumps(default_settings , indent=4)
                        file.write(data)
        else:
            print("File not found, using default settings.")
            ping = default_settings["ping"]
            theme = default_settings["theme"]
            debug = default_settings["debug"]
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

    def write_setting(self , type , value):
        default_settings = {"ping": "Tcping", "theme": "dark" , "debug":"off" }
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

        settings_icon_value = ft.icons.SETTINGS if self.page.theme_mode == ft.ThemeMode.DARK else ft.icons.SETTINGS_OUTLINED
        settings_icon = ft.IconButton(
            icon=settings_icon_value,
            icon_size=24,
            on_click=self.show_settings_dialog,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.BLACK,
                bgcolor=ft.colors.TRANSPARENT,
            ),
            tooltip="Settings"
        )

        import_button = ft.ElevatedButton(
            "Import Subscription",
            on_click=self.show_import_dialog,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.colors.WHITE,
                    ft.ControlState.HOVERED: ft.colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.colors.BLUE,
                    ft.ControlState.HOVERED: ft.colors.BLUE_700,
                },
            )
        )

        header = ft.Row(
            controls=[import_button, ft.Container(expand=1), settings_icon],  # container with expand fill the space bitween buttons
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # set two button in two side
        )

        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"XC (Xray-Client)", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"XC Version: {self.backend.version}", size=16),
                    ft.Text(f"Xray Version: {self.backend.xray_version}", size=16),
                    ft.Divider(),
                    *[ft.Text(f"{key}: {value}", size=14) for key, value in system_info.items()],
                ]),
                padding=20,
            ),
            elevation=5,
        )

        self.xray_button = ft.ElevatedButton(
            "Start Xray",
            on_click=self.toggle_xray,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.colors.WHITE,
                    ft.ControlState.HOVERED: ft.colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.colors.GREEN,
                    ft.ControlState.HOVERED: ft.colors.GREEN_700,
                },
            )
        )

        self.mode_switch = ft.Switch(
            label="Proxy",
            value=True,
            active_color=ft.colors.TRANSPARENT,
            #inactive_color=ft.colors.GREY,
            on_change=self.toggle_mode
        )

        self.log_view = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
            min_lines=10,
            max_lines=20,
            border_color=ft.colors.BLUE_200,
        )

        home_content = ft.Column([
            info_card,
            ft.Container(height=20),
            ft.Row([
                self.xray_button,
                self.mode_switch
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Text("Xray Logs:", size=18, weight=ft.FontWeight.BOLD),
            self.log_view
        ], expand=True, spacing=10)

        self.tabs.tabs[0].content = home_content

        for profile in self.backend.get_profiles():
            self.add_profile_tab(profile)

        # add header and tabs to page
        self.page.add(header, self.tabs)
        self.log("XC - Created By wikm , 3ircle with ❤️")
        self.check_for_updates()


    def add_profile_tab(self, profile):
        configs = self.backend.get_configs(profile)
        config_list = ft.ListView(expand=1, spacing=0, padding=20)

        for config in configs:
            config_list.controls.append(self.create_config_tile_with_ping(config, profile))

        update_button = ft.ElevatedButton("Update", on_click=lambda _: self.update_subscription(profile))
        delete_button = ft.ElevatedButton("Delete", on_click=lambda _: self.delete_subscription(profile))
        self.ping_all_button = ft.ElevatedButton(
            "Ping All", 
            on_click=lambda _: self.ping_button(profile, config_list)
        )

        tab_content = ft.Column([
            ft.Row([update_button, delete_button, self.ping_all_button]), #ft.Row([update_button, delete_button, ping_all_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            config_list
        ], expand=True)

        self.tabs.tabs.append(ft.Tab(text=profile, content=tab_content))
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

        debug_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("on"),
                ft.dropdown.Option("off"),
            ],
            value=self.debug_mod,
            on_change=self.change_debug,
            expand=True,
        )

        settings_dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Text("Ping Type : "), ping_type_dropdown], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("Theme : "), theme_dropdown], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("debug : "), debug_dropdown], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    spacing=20,
                ),
                padding=20,
                width=400,
            ),
            actions=[ft.TextButton("Close", on_click=lambda _: self.close_dialog(settings_dialog))],
        )

        # open setting page
        self.page.overlay.append(settings_dialog)
        settings_dialog.open = True
        self.page.update()


    def create_config_tile_with_ping(self, config, profile):
        is_selected = config == self.selected_config
        config_name = ft.Text(config, size=16, color=ft.colors.WHITE if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.BLACK)
        ping_text = ft.Text("Ping: -", size=16, color=ft.colors.WHITE if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.BLACK)

        return ft.ListTile(
            title=ft.Container(
                content=ft.Text(config, size=16),
                bgcolor=ft.colors.LIGHT_BLUE if is_selected else ft.colors.TRANSPARENT,
                padding=ft.padding.all(10),
                animate=ft.animation.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
                border_radius=10
            ),
            trailing=ft.Container(
                content=ping_text,
                padding=ft.padding.all(10)
            ),
            selected=is_selected,
            on_click=lambda _, c=config, p=profile: self.select_config(c, p)
        )


    # "0"  = cancel does not exist
    #  "1" = cancel showed
    #  "2" = camcel clicked   
    def ping_button(self, profile, config_list):
        if self.cancel_real_delay_stat == "0":
            self.ping_all_button.text = "Cancel"
            self.cancel_real_delay_stat = "1"
            self.ping_all_configs(profile, config_list)
        elif self.cancel_real_delay_stat == "1": 
            self.ping_all_button.text = "Ping All"
            self.cancel_real_delay_stat = "2"

    def ping_all_configs(self, profile, config_list):
        if self.ping_type == "Real-delay" :
            self.xray_button.disabled = True
            self.xray_button.text = "Start Xray"
            self.xray_button.style.bgcolor = {
                ft.ControlState.DEFAULT: ft.colors.GREEN,
                ft.ControlState.HOVERED: ft.colors.GREEN_700,
            }
        def ping_worker():
            self.cancel_real_delay_stat = "1" 
            for control in config_list.controls:
                if isinstance(control, ft.ListTile):
                    config_name = control.title.content.value
                    ping_text = control.trailing.content
                    config_num = config_name.split("-")[0].strip()
                    result = self.backend.ping_config(profile, config_num , self.ping_type)

                    if self.cancel_real_delay_stat == "2":
                        self.xray_button.disabled = False
                        break

                    ping_text.value = f"Ping: {result}"
                    self.page.update()

            # reset button txt
            self.ping_all_button.text = "Ping All"
            self.cancel_real_delay_stat = "0"
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

    def refresh_profile_tab(self, profile):
        if profile == "all":
            profiles = self.backend.get_profiles()
            for profile in profiles:
                for tab in self.tabs.tabs:
                    if tab.text == profile:
                        configs = self.backend.get_configs(profile)
                        config_list = tab.content.controls[1]
                        config_list.controls = [self.create_config_tile_with_ping(config, profile) for config in configs]
        
        for tab in self.tabs.tabs:
            if tab.text == profile:
                configs = self.backend.get_configs(profile)
                config_list = tab.content.controls[1]
                for control in config_list.controls:
                    config_name = control.title.content.value
                    # change color to selcted
                    if config_name == self.selected_config:
                        control.title.content.bgcolor = ft.colors.LIGHT_BLUE
                    else:
                        control.title.content.bgcolor = ft.colors.TRANSPARENT
                # just add new config
                for config in configs:
                    if not any(control.title.content.value == config for control in config_list.controls):
                        config_list.controls.append(self.create_config_tile_with_ping(config, profile))
                        
                break
        self.page.update()

    def show_import_dialog(self, e):
        def import_sub(e):
            name = name_field.value
            url = url_field.value
            if name and url:
                self.backend.import_subscription(name, url)
                self.add_profile_tab(name)
                dialog.open = False
                self.page.update()

        name_field = ft.TextField(label="Profile Name")
        url_field = ft.TextField(label="URL")
        dialog = ft.AlertDialog(
            title=ft.Text("Import Subscription"),
            content=ft.Column([name_field, url_field], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                ft.TextButton("Import", on_click=import_sub),
            ],
        )
        self.page.overlay.append(dialog)
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
                self.xray_button.text = "Stop Xray"
                self.xray_button.style.bgcolor = {
                    ft.ControlState.DEFAULT: ft.colors.RED,
                    ft.ControlState.HOVERED: ft.colors.RED_700,
                }
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
            self.xray_button.text = "Start Xray"
            self.xray_button.style.bgcolor = {
                ft.ControlState.DEFAULT: ft.colors.GREEN,
                ft.ControlState.HOVERED: ft.colors.GREEN_700,
            }
            self.log(message)
        self.page.update()

    def handle_xray_start(self, message):
        self.log(message)
        if "Successfully" in message or "Xray started successfully" in message:
            self.xray_button.text = "Stop Xray"
            self.xray_button.style.bgcolor = {
                ft.ControlState.DEFAULT: ft.colors.RED,
                ft.ControlState.HOVERED: ft.colors.RED_700,
            }

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
        
    def update_subscription(self , profile) :
        self.backend.update_subscription(profile)
        self.refresh_profile_tab(profile)
    def delete_subscription(self , profile) :
        self.backend.delete_subscription(profile)
        self.tabs.tabs = [tab for tab in self.tabs.tabs if tab.text != profile]
        self.refresh_profile_tab(profile)

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