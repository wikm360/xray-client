import requests
import base64
import json
import os
import shutil
import subprocess
import signal
import sys
import platform
from pathlib import Path

os_sys = "win"

def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Terminating Xray...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def get_sub():
    url = input("Please Enter your URL link (sub): ")
    sub_name = input("Please Enter your sub name: ")
    headers = {"user-agent": "v2rayNG"}
    r = requests.get(url=url, headers=headers)
    text = r.text
    decoded_bytes = base64.b64decode(text)
    decoded_str = decoded_bytes.decode('utf-8')
    list_configs = decoded_str.split("\n")
    
    directory_path = f"./subs/{sub_name}"
    folder_path = Path(directory_path)
    if folder_path.exists() and folder_path.is_dir() :
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error {file_path}: {e}")
        print(f"Previous {sub_name} sub deleted ...")
    
    if not folder_path.exists() :
        print("MAKE FOLDER")
        os.mkdir(directory_path)
    
    count = 0
    dict_name = {}
    for config in list_configs:
            import convert
            config_json, config_name = convert.convert(config)
            if config_name != "False":
                with open(f"./subs/{sub_name}/{count}.json", "w") as f:
                    f.write(config_json)
                
                dict_name[count] = config_name
                count += 1
    
    with open(f"./subs/{sub_name}/list.json", "w", encoding="utf-8") as f:
        json.dump(dict_name, f, ensure_ascii=False, indent=4)

def list_subs():
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    if directories:
        for i, sub in enumerate(directories, 1):
            print(f"{i} - {sub}")
        print("'add' for add new sub link")
        print("'exit' for back to main menu")
    else :
        print("No Sub detected ...")
        print("'exit' for back to main menu")
    choose = input("Enter your choice (sub name): ").lower()
    if choose == "add":
        get_sub()
    elif choose == "exit":
        pass  # back to main menu
    else:
        if choose in directories:
            list_configs(choose)
        else:
            print("Please enter a valid option ...")
            list_subs()

def list_configs(sub_name):
    global os_sys
    path_json = f"./subs/{sub_name}"
    list_file = [f for f in os.listdir(path_json) if f.endswith('.json') and f == "list.json"]
    if list_file:
        print(f"List of configs for {sub_name}:")
        with open(path_json+"/list.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        for key , value in data.items() :
            print(f"{key} - {value}")
        print("'exit' for back to main menu")
        choose_2 = input("Enter the config number to select: ").lower()
        if choose_2 == "exit":
            pass
        else:
            try:
                config_index = int(choose_2)
                if 0 <= config_index < len(data):
                    with open(f"./core/{os_sys}/select.txt", "w") as f:
                        f.write(f"./subs/{sub_name}/{config_index}.json")
                    print(f"Config {config_index} selected.")
                else:
                    print("Please enter a valid config number.")
                    list_configs(sub_name)
            except ValueError:
                print("Invalid input. Please enter a number.")
                list_configs(sub_name)
    else:
        print("No configs detected ...")

def run_xray():
    global os_sys
    with open(f"./core/{os_sys}/select.txt", "r") as f:
        config_path = f.read().strip()
    print(f"Running Xray with config: {config_path}")
    xray_path = f"./core/{os_sys}/xray"
    subprocess.Popen([xray_path, '-config', config_path])


def main_menu():
    global os_sys
    system_os = platform.system()
    if system_os == "Windows" :
        os_sys = "win"
    elif system_os == "Linux" :
        os_sys = "linux"
    elif system_os == "Darwin" :
        os_sys = "macos"
        
    
    while True:
        print(f"## OS detected = {os_sys} ##")

        select_path = f"./core/{os_sys}/select.txt"
        with open (select_path  , "r") as f :
            data = f.readlines()
            select = data[0].split("/")
            sub_select = select[2]
            config_select = select[3].split(".")[0]

        print("\nMain Menu:")
        print(f"1. Add new subscription")
        print(f"2. List of subscriptions / change sub or config (selected = {sub_select} -> {config_select})")
        print("3. Run")
        print("4. Exit")
        choice = input("Choose an option: ").lower()
        if choice == "1":
            get_sub()
        elif choice == "2":
            list_subs()
        elif choice == "3" :
            run_xray()
        elif choice == "4":
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()
