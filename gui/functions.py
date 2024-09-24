import os
import sys
from tkinter import messagebox
import requests
import shutil
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import convert
import json

def on_entry_click(event, entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, "end")
        entry.config(fg='black')

def on_focusout(event, entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg='grey')


def Import_btn(url_box):
    print(url_box.get())
def add_list(List:list, list_box):
    for i in List:
        list_box.insert('end', i)
def sub_refresh(profile_list):
    l = []
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    
    if directories:
        for sub in directories:
            l.append(sub)

    profile_list.delete(0, 'end')
    add_list(l, profile_list)

def get_sub(left_box,right_box):
    sub_url = right_box.get()
    sub_name = left_box.get()

    if not sub_url or not sub_name:
        messagebox.showwarning("Warning", "Please fill in all fields.")
        return

    headers = {"user-agent": "v2rayNG"}
    try:
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
        
        with open(f"./subs/{sub_name}/list.json", "w", encoding="utf-8") as f:
            json.dump(dict_name, f, ensure_ascii=False, indent=4)
        
        messagebox.showinfo("Success", f"Subscription {sub_name} added successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))
