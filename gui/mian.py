from tkinter import *
from functions import *
import json

theme_mode = "dark_mode"


with open("./var.json","r") as f:
    var_json = json.loads(f.read())
root = Tk()

root.geometry("900x600")
root.title(var_json["title"])
root.config(bg=var_json[theme_mode]["bg"])


url_box = Entry(root,font=("Helvetica", 13))
url_box.place(relx=0.019440124,rely=0.021879022,relwidth=0.461119751,relheight=0.069498069)

import_btn = Button(root,text="import",command=Import_btn,bg=var_json[theme_mode]["import_btn"])
import_btn.place(relx=0.488335925,rely=0.021879022,relwidth=0.081648523,relheight=0.069498069)













root.mainloop()
