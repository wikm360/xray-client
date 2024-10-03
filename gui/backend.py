import platform
import os
from tkinter import END,messagebox
import json
import subprocess
import threading
import requests
import base64
import shutil
import convert

# variable defenition :
xray_process = None
sub = ""

def add_list(List:list,list_box):
    for i in List:
        list_box.insert(END,i)

def set_sub(profile_name) :
    global sub
    sub = profile_name

def os_det():
    global os_sys
    system_os = platform.system()
    if system_os == "Windows" :
        os_sys = "win"
    elif system_os == "Linux" :
        os_sys = "linux"
    elif system_os == "Darwin" :
        os_sys = "macos"

def config_selected(config_list, console):
    selection = config_list.curselection()
    if not selection:
        log("No config selected.", console)
        return
    
    config_name = config_list.get(selection)
    profile_name = sub
    
    try:
        os_det()
        config_num = config_name.split("-")[0]
        config_index = int(config_num)
        with open(f"./core/{os_sys}/select.txt", "w") as f:
            f.write(f"./subs/{profile_name}/{config_index}.json")
        log(f"Config {config_index} selected.", console)
    except Exception as e:
        log(f"Error selecting config: {str(e)}", console)

def profile_selected(profile_list, config_list, console):
    selection = profile_list.curselection()
    if not selection:
        log("No profile selected.", console)
        return

    profile_name = profile_list.get(selection)
    set_sub(profile_name)

    path_json = f"./subs/{profile_name}/list.json"
    if os.path.exists(path_json):
        with open(path_json, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        config_list.delete(0, END)
        for key, value in data.items():
            config_list.insert(END, f"{key} - {value}")
    else:
        messagebox.showinfo("Info", "No configs detected.")
        log("No configs detected for the selected profile.", console)


def log(message, console):
    console.config(state="normal")
    console.insert(END, message + "\n")
    console.config(state="disabled")
    console.see(END)

def sub_refresh(profile_list):
    l = []
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    
    if directories:
        for sub in directories:
            l.append(sub)

    profile_list.delete(0, 'end')
    add_list(l, profile_list)

def get(name , url) :
    sub_url = url
    sub_name = name

    if not sub_url or not sub_name:
        messagebox.showwarning("Warning", "Please fill in all fields.")
        return

    headers = {"user-agent": "v2rayNG"}
    r = requests.get(url=sub_url, headers=headers)
    text = r.text
    decoded_bytes = base64.b64decode(text)
    decoded_str = decoded_bytes.decode('utf-8')
    list_configs = decoded_str.split("\n")
    
    directory_path = f"./subs/{sub_name}"
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        shutil.rmtree(directory_path)
        messagebox.showinfo("Success", f"Previous {sub_name} sub deleted ...")

    os.mkdir(directory_path)

    dict_name = {}
    for count, config in enumerate(list_configs):
        if config.strip():
            config_json, config_name = convert.convert(config)
            if config_name != "False":
                with open(f"./subs/{sub_name}/{count}.json", "w") as f:
                    f.write(config_json)
                dict_name[count] = config_name

def Update_btn(list_box ,  console , profile_list , config_list):
    selection = list_box.curselection()
    if selection :
        sub_name = list_box.get(selection)
        path = f"./subs/{sub_name}/url.txt"
        with open (path,"r") as f :
            url_list = f.readlines()
            url = url_list[0]
        try:
            get(sub_name , url)
            sub_refresh(profile_list)
            config_refresh(config_list)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else :
        log("Please select one subsciption" , console)

def config_refresh (config_list) :
    config_list.delete(0, END)

def run_xray(console):
    global xray_process
    os_det()  # Assuming this sets the correct OS settings

    if xray_process is None:
        try:
            with open(f"./core/{os_sys}/select.txt", "r") as f:
                config_path = f.read().strip()

            xray_path = f"./core/{os_sys}/xray"

            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            # Start the Xray process
            xray_process = subprocess.Popen(
                [xray_path, '-config', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )

            messagebox.showinfo("Success", f"Xray is running with config: {config_path}")

            # Start a thread to read logs (assume read_logs handles console output)
            threading.Thread(target=read_logs, args=(xray_process, console), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

# def close_xray():
#     global xray_process
#     xray_process.terminate()
#     xray_process = None
def close_xray():
    global xray_process
    if xray_process:
        xray_process.terminate()
        xray_process = None
        messagebox.showinfo("Xray", "Xray has been stopped.")

def read_logs(process, console):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            log(output.strip(), console)
