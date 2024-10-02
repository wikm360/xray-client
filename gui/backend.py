import platform
import os
from tkinter import END,messagebox
import json
import time

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



def config_selected(config_list,console):
            print(config_list.get(config_list.curselection()))
            profile_name = sub
            if config_list.get(config_list.curselection()):
                config_name = config_list.get(config_list.curselection())
            else:
                 return None
            try:
                os_det()
                config_num = config_name.split("-")[0]
                try:
                    config_index = int(config_num)
                    with open(f"./core/{os_sys}/select.txt", "w") as f:
                        f.write(f"./subs/{profile_name}/{config_index}.json")
                    log(f"Config {config_index} selected.",console)

                except ValueError:
                    print("Invalid input. Please enter a number.")
            except Exception as  e:
                log(e,console)

def profile_selected(profile_list,config_list,console):


    profile_name = profile_list.get(profile_list.curselection())
    print(profile_name)
    set_sub(profile_name)
    if not profile_name:
        messagebox.showwarning("Warning", "Please select a subscription first.")
        return

    path_json = f"./subs/{profile_name}/list.json"
    if os.path.exists(path_json):
        with open(path_json, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        config_list.delete(0, END)
        l =[]
        for key, value in data.items():
            l.append(f"{key} - {value}")
        add_list(l,config_list)
        log(f"profile : {profile_name} selected <3",console)
        #X Error of failed request:  BadLength (poly request too large or internal Xlib length error)
        #Major opcode of failed request:  139 (RENDER)
        #Minor opcode of failed request:  20 (RenderAddGlyphs)
        #Serial number of failed request:  1124
        #Current serial number in output stream:  1171
    else:
        messagebox.showinfo("Info", "No configs detected.")


def log(message, console):
    console.config(state="normal")  # باز کردن حالت برای اضافه کردن لاگ
    console.insert(END, message + "\n")  # افزودن لاگ به انتهای کنسول
    console.config(state="disabled")  # غیرفعال کردن دوباره ویرایش
    console.see(END)  # برای نمایش اتوماتیک لاگ جدید در پایین صفحه




def sub_refresh(profile_list):
    l = []
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    
    if directories:
        for sub in directories:
            l.append(sub)

    profile_list.delete(0, 'end')
    add_list(l, profile_list)
