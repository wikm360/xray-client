from pathlib import Path
from tkinter import *
from backend import *

OUTPUT_PATH = Path(__file__).parent
print(OUTPUT_PATH)
ASSETS_PATH = OUTPUT_PATH / Path(r"./assets/frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)
def toggle_switch(button, console):
    if button['image'] == str(button_image_off):
        button.config(image=button_image_on)
        run_xray(console)
        log("Xray started...\n" , console)
    else:
        button.config(image=button_image_off)
        close_xray()
        log("Xray stopped...\n" , console)
def on_close():
    if messagebox.askokcancel("Quit", "Do you want to exit the program?"):
        close_xray()
        window.destroy()


#================= main page setting ==============#


window = Tk()
window.title("XC(Xray-Cient)")
#windows icon
# window.iconbitmap(str(ASSETS_PATH) + "/icon.ico")

window.geometry("836x513")
window.configure(bg="#0C0C0C")
window.resizable(False, False)


#================= import page ===================#


import_page = Toplevel()
import_page.geometry("600x300")
import_page.config(bg="#0C0C0C")
import_page.title("import profile")
import_page.resizable(False, False)


name_label = Label(import_page,text="PROFILE NAME :",font=("calibri",15,"bold"),bg="#0C0C0C",fg="#ffffff")
name_label.place(x=12,y=12)


name_var = StringVar()
name_box = Entry(import_page,textvariable=name_var)
name_box.place(x=12,y=45,width=260,height=32)

url_label = Label(import_page,text="URL :",font=("calibri",15,"bold"),bg="#0C0C0C",fg="#ffffff")
url_label.place(x=12,y=120)

url_var = StringVar()
url_box = Entry(import_page,textvariable=url_var)
url_box.place(x=12,y=153,width=520,height=32)

paste_img = PhotoImage(file=relative_to_assets("paste_btn.png"))
paste_btn = Button(import_page,image=paste_img, borderwidth=0, highlightthickness=0, command=lambda: Clipboard(url_var), relief="flat")
paste_btn.place(x=536,y=153,width=32,height=32)


button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
import_btn2 = Button(import_page,image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: Import(name_var,url_box,profile_list,import_page,import_btn,console), relief="flat")
import_btn2.place(x=12, y=200, width=94, height=39)

cancel_img = PhotoImage(file=relative_to_assets("button_4.png"))
cancel_btn = Button(import_page,image=cancel_img, borderwidth=0, highlightthickness=0, command=lambda :on_close_import(import_page,import_btn,url_var,name_var), relief="flat")
cancel_btn.place(x=150, y=200, width=94, height=39)

import_page.withdraw()


#================= main elements setup ===================#

canvas = Canvas(window, bg="#0C0C0C", height=513, width=836, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)


import_btn = Button(window,image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: Import_btn(import_page,import_btn), relief="flat")
import_btn.place(x=37.0, y=23.0, width=94.0, height=39.0)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
update_btn = Button(image=button_image_2, borderwidth=0, highlightthickness=0, command=lambda:Update_btn(profile_list ,  console , profile_list , config_list), relief="flat")
update_btn.place(x=156.0, y=23.0, width=94.0, height=39.0)

button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
remove_btn = Button(image=button_image_3, borderwidth=0, highlightthickness=0, command=lambda:Delete_btn(profile_list ,console, profile_list , config_list), relief="flat")
remove_btn.place(x=275.0, y=23.0, width=94.0, height=39.0)



button_image_off = PhotoImage(file=relative_to_assets("button_off.png"))
button_image_on = PhotoImage(file=relative_to_assets("button_on.png"))
start_btn = Button(image=button_image_off, borderwidth=0, highlightthickness=0, 
                   command=lambda: toggle_switch(start_btn, console), relief="flat")
start_btn.place(x=704.0, y=23.0, width=94.0, height=39.0)

console = Text(window, bg="#333333", fg="#FFFFFF", font=("Helvetica", 12), bd=0, highlightthickness=1,
              highlightbackground="#444444")
console.place(x=275, y=361, width=512, height=137)
console_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
console_scroll.place(x=790, y=361, width=8, height=137)
console.config(yscrollcommand=console_scroll.set)
console_scroll.config(command=console.yview)

console.bind("<Key>", lambda e: "break")
console.bind("<Control-c>", lambda e: console.event_generate('<<Copy>>'))



profile_list = Listbox(window, selectbackground="#2d9bf0", font=("Helvetica", 16, "normal"),
                       bg="#333333", fg="#FFFFFF", bd=0, highlightthickness=1, relief="flat",
                       selectforeground="#FFFFFF", highlightbackground="#444444")
profile_list.place(x=37, y=83, width=210, height=415)
profile_list.bind("<<ListboxSelect>>", lambda event: profile_selected(profile_list, config_list ,console))

profile_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
profile_scroll.place(x=251, y=83, width=8, height=415)
profile_list.config(yscrollcommand=profile_scroll.set)
profile_scroll.config(command=profile_list.yview)

config_list = Listbox(window, selectbackground="#2d9bf0", font=("egoe UI Emoji", 14, "normal"),
                      bg="#333333", fg="#FFFFFF", bd=0, highlightthickness=1, relief="flat",
                      selectforeground="#FFFFFF", highlightbackground="#444444")
config_list.place(x=275, y=83, width=512, height=271)

config_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
config_scroll.place(x=790, y=83, width=8, height=271)
config_list.config(yscrollcommand=config_scroll.set)
config_scroll.config(command=config_list.yview)
config_list.bind("<<ListboxSelect>>", lambda event: config_selected(config_list, console))



log("XC(Xray-Client) Ver 3.0", console=console)
log("Created by wikm, 3ircle with ❤️", console=console)

sub_refresh(profile_list)


window.protocol("WM_DELETE_WINDOW", on_close)
import_page.protocol("WM_DELETE_WINDOW", func=lambda :on_close_import(import_page,import_btn,url_var,name_var))
window.mainloop()
