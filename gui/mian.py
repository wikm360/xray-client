from tkinter import *
from functions import *
import json

theme_mode = "light_mode"


with open("./setting.json","r") as f:
    var_json = json.loads(f.read())
root = Tk()



root.geometry("900x600")
root.title(var_json["title"])
root.config(bg=var_json[theme_mode]["bg"])


url_box = Entry(root,font=("Helvetica", 13))
url_box.place(relx=0.019440124,rely=0.021879022,relwidth=0.461119751,relheight=0.069498069)

import_btn = Button(root,text="import",command=lambda:Import_btn(url_box),bg=var_json[theme_mode]["import_btn"])
import_btn.place(relx=0.488335925,rely=0.021879022,relwidth=0.081648523,relheight=0.069498069)

profile_list = Listbox(root,selectbackground="#2d9bf0",font=("Helvetica",20),border=5)
profile_list.place(relx=0.020217729,rely=0.145431145,relwidth=0.239502333,relheight=0.791505792)
l = ["profile 1","profile 2","profile 3","profile 4","profile 5"]

add_list(l,profile_list)








root.mainloop()
