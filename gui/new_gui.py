 # /home/wikmgg/Documents/GitHub/xray-client/gui/assets/frame0
from pathlib import Path
from tkinter import *
from backend import *

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"./assets/frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


window = Tk()

window.geometry("836x513")
window.configure(bg="#0C0C0C")
window.resizable(False, False)

canvas = Canvas(window, bg="#0C0C0C", height=513, width=836, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# Buttons setup
button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
import_btn = Button(image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: print("button_1 clicked"), relief="flat")
import_btn.place(x=37.0, y=23.0, width=94.0, height=39.0)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
update_btn = Button(image=button_image_2, borderwidth=0, highlightthickness=0, command=lambda: print("button_2 clicked"), relief="flat")
update_btn.place(x=156.0, y=23.0, width=94.0, height=39.0)

button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
remove_btn = Button(image=button_image_3, borderwidth=0, highlightthickness=0, command=lambda: print("button_3 clicked"), relief="flat")
remove_btn.place(x=275.0, y=23.0, width=94.0, height=39.0)

button_image_4 = PhotoImage(file=relative_to_assets("button_4.png"))
start_btn = Button(image=button_image_4, borderwidth=0, highlightthickness=0, command=lambda: print("button_4 clicked"), relief="flat")
start_btn.place(x=704.0, y=23.0, width=94.0, height=39.0)

console = Text(window, bg="#333333", fg="#FFFFFF", font=("Helvetica", 12), bd=0, highlightthickness=1,
              highlightbackground="#444444")
console.place(x=275, y=361, width=512, height=137)
console_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
console_scroll.place(x=790, y=361, width=8, height=137)
console.config(yscrollcommand=console_scroll.set)
console_scroll.config(command=console.yview)

# غیرفعال کردن امکان ویرایش و فقط امکان کپی کردن
console.bind("<Key>", lambda e: "break")  # غیرفعال کردن همه کلیدها به جز کپی
console.bind("<Control-c>", lambda e: console.event_generate('<<Copy>>'))  # اجازه کپی کردن



# Profile Listbox (Minimal Design)
profile_list = Listbox(window, selectbackground="#2d9bf0", font=("Helvetica", 16, "normal"),
                       bg="#333333", fg="#FFFFFF", bd=0, highlightthickness=1, relief="flat",
                       selectforeground="#FFFFFF", highlightbackground="#444444")
profile_list.place(x=37, y=83, width=210, height=415)
profile_list.bind("<<ListboxSelect>>", lambda event: profile_selected(profile_list, config_list ,console))

profile_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
profile_scroll.place(x=251, y=83, width=8, height=415)
profile_list.config(yscrollcommand=profile_scroll.set)
profile_scroll.config(command=profile_list.yview)

# Config Listbox (Minimal Design)
config_list = Listbox(window, selectbackground="#2d9bf0", font=("egoe UI Emoji", 14, "normal"),
                      bg="#333333", fg="#FFFFFF", bd=0, highlightthickness=1, relief="flat",
                      selectforeground="#FFFFFF", highlightbackground="#444444")
config_list.place(x=275, y=83, width=512, height=271)

config_scroll = Scrollbar(window, orient=VERTICAL, bg="#444444", troughcolor="#222222", bd=0, highlightthickness=0)
config_scroll.place(x=790, y=83, width=8, height=271)
config_list.config(yscrollcommand=config_scroll.set)
config_scroll.config(command=config_list.yview)
config_list.bind("<<ListboxSelect>>",lambda event:config_selected(config_list,console))
# Console (Read-Only)



# Add initial logs
log("XC(Xray-Client) Ver 2.3", console=console)
log("Created by wikm, 3ircle with ❤️", console=console)

# Refreshing profile list
sub_refresh(profile_list)

window.mainloop()
