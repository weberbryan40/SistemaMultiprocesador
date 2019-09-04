from clock import *
import time 

cycle_time = 6

clock = Clock(1,cycle_time)
clock.initialize_clock()

caches = []

root = Tk()
root.title('Cache'+str(1))
root.geometry("400x340") 

tv = Treeview(root,height = 8)
tv['columns'] = ('valid', 'tag', 'data')
tv.heading("#0", text='Address')
tv.column("#0", anchor="center",width=100)
tv.heading('valid', text='Valid')
tv.column('valid', anchor='center', width=100)
tv.heading('tag', text='Tag')
tv.column('tag', anchor='center', width=100)
tv.heading('data', text='Data')
tv.column('data', anchor='center', width=100)
tv.grid(sticky = (N,S,W,E))
treeview = tv
caches.append(treeview)

for i in range(8):
    treeview.insert('', 'end','block'+str(i), text=str(i), values=('0','0','0'))

       
while True:
    caches_info=clock.get_cache_data()

    for i in range(4):
        if caches_info[i] != []:
            for j in range(8):
                caches[i].item('block'+str(j),values=(str(caches_info[i][j][0]),str(caches_info[i][j][1]),str(caches_info[i][j][2])))      
    time.sleep(cycle_time)

