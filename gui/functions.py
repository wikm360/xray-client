def Import_btn(url_box):
    print(url_box.get())
def add_list(List:list,list_box):
    c = 1
    for i in List:
        list_box.insert(c,i)
        c +=1