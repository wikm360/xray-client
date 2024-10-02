from tkinter import *
from functions import *
import json

#Defs
def on_select(event, profile_list, config_list, sub):
    selection = profile_list.curselection()
    if selection:
        selected_value = profile_list.get(selection)
        list_configs(event, selected_value, config_list, sub)


with open("./setting.json","r") as f:
    var_json = json.loads(f.read())


theme_mode = var_json["mode"]


root = Tk()
<<<<<<< Updated upstream
# print(os.path.isfile("./gui/XC.ico"))
# root.iconbitmap("./gui/XC.ico")
=======
# root.iconbitmap("XC.ico")
>>>>>>> Stashed changes

consol_text = StringVar()

sub = StringVar()
root.geometry("900x600")
root.title(var_json["title"])
root.config(bg=var_json[theme_mode]["bg"])


import_btn = Button(root,text="import",font=("calibri",10,"bold"),command=lambda:Import_btn(import_btn,Toplevel,Button,DISABLED,NORMAL,var_json,theme_mode,Entry,Label,StringVar,profile_list , consol),bg=var_json[theme_mode]["import_btn"],fg=var_json[theme_mode]["text"])
import_btn.place(relx=0.02,rely=0.02,relwidth=0.08,relheight=0.07)

update_btn = Button(root,text="update",font=("calibri",10,"bold"),command=lambda:Update_btn(profile_list ,  consol , profile_list , config_list),bg=var_json[theme_mode]["update_btn"],fg=var_json[theme_mode]["text"])
update_btn.place(relx=0.12 ,rely=0.02,relwidth=0.08,relheight=0.07)

delete_btn = Button(root,text="delete",font=("calibri",10,"bold"),command=lambda:Delete_btn(profile_list ,consol, profile_list , config_list),bg=var_json[theme_mode]["delete_btn"],fg=var_json[theme_mode]["text"])
delete_btn.place(relx=0.22,rely=0.02,relwidth=0.08,relheight=0.07)

start_btn =Button(root,text="off",font=("calibri",10,"bold"),command=lambda:toggle_switch(start_btn , consol),bg="red")
start_btn.place(relx=0.9,rely=0.02,relwidth=0.08,relheight=0.07)

profile_list = Listbox(root,selectbackground="#2d9bf0",font=("Helvetica",20,"bold"),border=5,bg=var_json[theme_mode]["list_bg"],fg=var_json[theme_mode]["text"])
profile_list.place(relx=0.020217729,rely=0.145431145,relwidth=0.239502333,relheight=0.791505792)
profile_list.bind("<<ListboxSelect>>", lambda event: on_select(event, profile_list, config_list, sub))
#profile_list.bind("<<ListboxSelect>>", lambda event: list_configs(event,profile_list.get(profile_list.curselection()),config_list,sub))



profile_scroll = Scrollbar(root,orient=VERTICAL)
profile_scroll.place(relx=0.265940902,rely=0.145431145,relwidth=0.022550544,relheight=0.791505792)
profile_list.config(yscrollcommand=profile_scroll.set)
profile_scroll.config(command=profile_list.yview)

sub_refresh(profile_list)


config_list = Listbox(root,selectbackground="#2d9bf0",font=("Helvetica",15,"bold"),border=5,bg=var_json[theme_mode]["list_bg"],fg=var_json[theme_mode]["text"])
config_list.place(relx=0.295489891,rely=0.145431145,relwidth=0.6718507,relheight=0.518661519)
config_list.bind("<<ListboxSelect>>",lambda  event :select_config(event,config_list.get(config_list.curselection()),sub , consol))

config_scroll = Scrollbar(root,orient=VERTICAL)
config_scroll.place(relx=0.97,rely=0.145431145,relwidth=0.022550544,relheight=0.518661519)
config_list.config(yscrollcommand=config_scroll.set)
config_scroll.config(command=config_list.yview)

consol = Text(root,bg=var_json[theme_mode]["list_bg"],fg=var_json[theme_mode]["text"],border=5)
consol.place(relx=0.295489891,rely=0.67431145,relwidth=0.675,relheight=0.2578)
log("XC(Xray-Client) Ver 2.2" , console=consol)
log("Created by wikm , 3ircle with ❤️" , console=consol)

consol_scroll = Scrollbar(root,orient=VERTICAL)
consol_scroll.place(relx=0.97,rely=0.67431145,relwidth=0.022550544,relheight=0.2578)
consol.config(yscrollcommand=consol_scroll.set)
consol_scroll.config(command=consol.yview)


root.mainloop()
