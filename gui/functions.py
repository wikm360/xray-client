from tkinter import messagebox ,END
import requests
import os 
import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import base64
import platform
import shutil
import convert
import json
import subprocess
import threading
import pyperclip


xray_process = None

offset_x = 0
offset_y = 0
url_var = ""
error_var = ""

def close(page , btn , NORMAL):
    btn.config(state=NORMAL)
    page.destroy()

def Import_btn(btn, Toplevel, Button, DISABLED, NORMAL, var_json, theme_mode, Entry, Lable, StringVar, profile_list):
    global url_var, error_var
    btn.config(state=DISABLED)
    import_page = Toplevel()
    import_page.withdraw()
    import_page.overrideredirect(True)
    import_page.geometry("600x300")
    import_page.config(bg=var_json[theme_mode]["bg"])
    
    import_page.bind("<Button-1>", start_move)
    import_page.bind("<B1-Motion>", lambda event: on_move(event, import_page))

    url_var = StringVar()
    error_var = StringVar()

    close_btn = Button(import_page, text="cancel", bg=var_json[theme_mode]["delete_btn"], 
                       fg=var_json[theme_mode]["text"], command=lambda: close(import_page, btn, NORMAL))
    close_btn.place(relx=0.4, rely=0.5, relwidth=0.3, relheight=0.2)

    import_btn = Button(import_page, text="import", bg=var_json[theme_mode]["import_btn"],
                        fg=var_json[theme_mode]["text"], command=lambda: Import(name_entry.get(), url_entry.get(), profile_list, import_page, btn, NORMAL))
    import_btn.place(relx=0.01, rely=0.5, relwidth=0.3, relheight=0.2)

    clipboard_btn = Button(import_page, text="P", bg=var_json[theme_mode]["update_btn"],
                           fg=var_json[theme_mode]["text"], command=lambda: Clipboard(url_var))
    clipboard_btn.place(relx=0.83, rely=0.27, relwidth=0.1, relheight=0.1)

    name_entry = Entry(import_page, bg=var_json[theme_mode]["bg"])
    name_entry.place(relx=0.01, rely=0.08, relwidth=0.3, relheight=0.1)

    name_lable = Lable(import_page, text="profile name :", font=("calibri", 10, "bold"),
                       bg=var_json[theme_mode]["bg"], fg=var_json[theme_mode]["text"])
    name_lable.place(relx=0.01, rely=0.005)

    url_entry = Entry(import_page, textvariable=url_var)
    url_entry.place(relx=0.01, rely=0.27, relwidth=0.8, relheight=0.1)

    url_lable = Lable(import_page, text="profile url :", font=("calibri", 10, "bold"),
                      bg=var_json[theme_mode]["bg"], fg=var_json[theme_mode]["text"])
    url_lable.place(relx=0.01, rely=0.2)

    erroe_lable = Lable(import_page, textvariable=error_var, font=("calibri", 10),
                        fg="red", bg=var_json[theme_mode]["bg"])
    erroe_lable.place(relx=0.01, rely=0.4)

    import_page.deiconify()


def add_list(List:list,list_box):
    c = 1
    for i in List:
        list_box.insert(c,i)
        c +=1
    
def Delete_btn(list_box):
    print(list_box)

def start_move(event):
    global offset_x, offset_y
    offset_x = event.x
    offset_y = event.y

def on_move(event,root):
    x = event.x_root - offset_x
    y = event.y_root - offset_y
    root.geometry(f'+{x}+{y}')

def Import(name,url,profile_list , import_page , btn , NORMAL):
        if not name:
            error_var.set("you have to enter a name")  
        elif not url :
            error_var.set("you have to enter a url")    
        else :
            sub_url = url
            sub_name = name

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
                sub_refresh(profile_list)
                close(import_page , btn , NORMAL)
            except Exception as e:
                messagebox.showerror("Error", str(e))


def Update_btn():
    pass


def Clipboard(string_var):
    copied_text = pyperclip.paste()
    string_var.set(copied_text)


def sub_refresh(profile_list):
    l = []
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    
    if directories:
        for sub in directories:
            l.append(sub)

    profile_list.delete(0, 'end')
    add_list(l, profile_list)

def list_configs(event,sub,config_listbox,sub_var):

    sub_var.set(sub)
    selected_sub = sub
    if not selected_sub:
        messagebox.showwarning("Warning", "Please select a subscription first.")
        return

    path_json = f"./subs/{selected_sub}/list.json"
    if os.path.exists(path_json):
        with open(path_json, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        
        config_listbox.delete(0, END)  # پاک کردن لیست قبلی
        for key, value in data.items():
            config_listbox.insert(END, f"{key} - {value}")
    else:
        messagebox.showinfo("Info", "No configs detected.")


def select_config(event,config_num,sub , console):
        try:
            os_det()
            choose_2 = config_num.split("-")[0]
            sub_name= sub.get()
            if choose_2 == "exit":
                pass
            else:
                try:
                    config_index = int(choose_2)
                    with open(f"./core/{os_sys}/select.txt", "w") as f:
                        f.write(f"./subs/{sub_name}/{config_index}.json")
                    print(f"Config {config_index} selected.")
                    log(f"Config {config_index} selected from {sub_name}" , console)
                except ValueError:
                    print("Invalid input. Please enter a number.")
        except Exception as  e:
            print("select config : " ,e, sep="  ")
            log(f"Error : {e}" , console)
def os_det():
    global os_sys
    system_os = platform.system()
    if system_os == "Windows" :
        os_sys = "win"
    elif system_os == "Linux" :
        os_sys = "linux"
    elif system_os == "Darwin" :
        os_sys = "macos"


def toggle_switch(switch_button , console):
    if switch_button.config('text')[-1] == 'off':
        switch_button.config(text='on', bg='green')
        run_xray(console)
    else:
        switch_button.config(text='off', bg='red')
        close_xray(console)

def run_xray(console):
    global xray_process
    os_det()

    if xray_process is None:
        try:
            with open(f"./core/{os_sys}/select.txt", "r") as f:
                config_path = f.read().strip()

            xray_path = f"./core/{os_sys}/xray"

            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            xray_process = subprocess.Popen(
                [xray_path, '-config', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )

            messagebox.showinfo("Success", f"Xray is running with config: {config_path}")

            threading.Thread(target=read_logs, args=(xray_process, console), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def close_xray(console):
    global xray_process
    xray_process.terminate()
    xray_process = None
    log("Xray Closed." , console)

def log(message, console):
    console.insert(END, message + "\n")
    console.see(END)

def read_logs(process, console):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            log(output.strip(), console)