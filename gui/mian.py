from tkinter import *
from functions import *
import json
import os

theme_mode = "light_mode"


with open("./setting.json","r") as f:
    var_json = json.loads(f.read())
root = Tk()



root.geometry("900x600")
root.title(var_json["title"])
root.config(bg=var_json[theme_mode]["bg"])


# url_box = Entry(root,font=("Helvetica", 13))
# url_box.place(relx=0.019440124,rely=0.021879022,relwidth=0.461119751,relheight=0.069498069)

def on_entry_click(event, entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, "end")
        entry.config(fg='black')

def on_focusout(event, entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg='grey')

left_box = Entry(root, font=("Helvetica", 13), fg='grey')
left_box.insert(0, "name")
left_box.bind("<FocusIn>", lambda event: on_entry_click(event, left_box, "name"))
left_box.bind("<FocusOut>", lambda event: on_focusout(event, left_box, "name"))
left_box.place(relx=0.019440124, rely=0.021879022, relwidth=0.3, relheight=0.069498069)

right_box = Entry(root, font=("Helvetica", 13), fg='grey')
right_box.insert(0, "subscription link")
right_box.bind("<FocusIn>", lambda event: on_entry_click(event, right_box, "subscription link"))
right_box.bind("<FocusOut>", lambda event: on_focusout(event, right_box, "subscription link"))
right_box.place(relx=0.32, rely=0.021879022, relwidth=0.45, relheight=0.069498069)

import_btn = Button(root, text="import", command=lambda: Import_btn(right_box), bg=var_json[theme_mode]["import_btn"])
import_btn.place(relx=0.77, rely=0.021879022, relwidth=0.081648523, relheight=0.069498069)


profile_list = Listbox(root,selectbackground="#2d9bf0",font=("Helvetica",20),border=5)
profile_list.place(relx=0.020217729,rely=0.145431145,relwidth=0.239502333,relheight=0.791505792)

l = []
path = "./subs"
directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
if directories:
    for i, sub in enumerate(directories, 1):
        l.append(sub)
# l = ["profile 1","profile 2","profile 3","profile 4","profile 5"]

add_list(l,profile_list)

root.mainloop()






root.mainloop()
