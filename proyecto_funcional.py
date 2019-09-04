try:
    from Tkinter import *
    from ttk import *
except ImportError:  # Python 3
    from tkinter import *
    from tkinter.ttk import *
import threading
import time
import random
from sys import stdout


#variables for logical part
cycle_time = 4
global_cycle = 0
execute_cpu_cycle = False
execution_units = []
memory = []
control = []
mem_bus = None

mutex_control_cache = threading.Lock()
mutex_cache = threading.Lock()

#variables for graphic part
cache_views=[]
control_views=[]
cpu_views=[]
memory_view = None
bus_view = None
clock_view = None

view_modifications_list = {'cpus':[None,None,None,None],
                           'caches':[None,None,None,None],
                           'controls':[None,None,None,None],
                           'bus':None,
                           'clock':None,
                           'memory':None
                           }

root = Tk()
root.title('Multiprocessor system')
root.geometry("1150x580")

#Hilo para controlador
def control_thread(cache):
    global execute_cpu_cycle,execution_units,mem_bus,view_modifications_list,global_cycle,control,control,mutex_cache
    cpu_list=[0,1,2,3]
    cpu_list.remove(cache)
    
    while True:
        mutex_control_cache.acquire()
        if len(control[cache]['cpus_notified']) == 3:
            control[cpu_list[0]]['invalidate_index'] = -1
            control[cpu_list[0]]['invalidate_tag'] = -1
            control[cpu_list[0]]['cpus_notified'] = []
        #stdout.write(str(cache)+': '+str(control[cpu_list[0]]['invalidate_index'])+','+str(control[cpu_list[0]]['invalidate_index'])+','+str(control[cpu_list[0]]['invalidate_index']))
        if control[cpu_list[0]]['invalidate_index'] != -1 and not cache in control[cpu_list[0]]['cpus_notified']:
            if execution_units[cache]['cache'][control[cpu_list[0]]['invalidate_index']]['tag']==control[cpu_list[0]]['invalidate_tag'] and \
                execution_units[cache]['cache'][control[cpu_list[0]]['invalidate_index']]['valid']==1:
                invalidate_cache_block(cache,control[cpu_list[0]]['invalidate_index'],cpu_list[0])
            control[cpu_list[0]]['cpus_notified'].append(cache)
        if control[cpu_list[1]]['invalidate_index'] != -1 and not cache in control[cpu_list[1]]['cpus_notified']:
            if execution_units[cache]['cache'][control[cpu_list[1]]['invalidate_index']]['tag']==control[cpu_list[1]]['invalidate_tag'] and \
                execution_units[cache]['cache'][control[cpu_list[1]]['invalidate_index']]['valid']==1:
                invalidate_cache_block(cache,control[cpu_list[1]]['invalidate_index'],cpu_list[1])
            control[cpu_list[1]]['cpus_notified'].append(cache)
        if control[cpu_list[2]]['invalidate_index'] != -1 and not cache in control[cpu_list[2]]['cpus_notified']:
            if execution_units[cache]['cache'][control[cpu_list[2]]['invalidate_index']]['tag']==control[cpu_list[2]]['invalidate_tag'] and \
                execution_units[cache]['cache'][control[cpu_list[2]]['invalidate_index']]['valid']==1:
                invalidate_cache_block(cache,control[cpu_list[2]]['invalidate_index'],cpu_list[2])
            control[cpu_list[2]]['cpus_notified'].append(cache)
        mutex_control_cache.release()
        
        if mem_bus['address'] != -1 and mem_bus['instruction_type'] == 'R':
            index=mem_bus['address']%8
            tag=mem_bus['address']//8
            if execution_units[cache]['cache'][index]['valid'] == 1 and execution_units[cache]['cache'][index]['tag'] == tag and execution_units[cache]['cache'][index]['modified'] == 1:
                    back_off_inst('CPU'+str(cache+1),mem_bus['address'])                    
                    update_cache(cache,index,tag,execution_units[cache]['cache'][index]['data'])
                    k = int(mem_bus['cpu_in_bus'][3])-1
                    control[k]['obs'] = 'CPU'+str(cache+1)
                    control[k]['action'] = 'Back_Off'
                    view_modifications_list['controls'][k] = {'obs':control[k]['obs'],'action':control[k]['action']}
            if not 'CPU'+str(cache+1) in mem_bus['cpus_notified']:
                mem_bus['cpus_notified'].append('CPU'+str(cache+1))
        
        time.sleep(0.1)

#Hilo para CPUs
def cpu_thread(index):
    global execute_cpu_cycle,execution_units,mem_bus,view_modifications_list,global_cycle
    id = execution_units[index]['cpu']['id']
    while True: 
        if execute_cpu_cycle:
            execution_units[index]['cpu']['cycles'] -= 1
        
            if execution_units[index]['cpu']['cycles'] <= 0:
                ##OJO: RECORDAR PONER EL STATUS DEL CPU
                execution_units[index]['cpu']['instruction'],execution_units[index]['cpu']['cycles'],execution_units[index]['cpu']['address'] = create_new_instruction()
                execution_units[index]['cpu']['status'] = 'Running'#POR AHORA
                reset_control(index)
                print(index)
                tag=execution_units[index]['cpu']['address']//8
                ind=execution_units[index]['cpu']['address']%8
                if execution_units[index]['cpu']['instruction'] == 'W':
                    value = write_cache(index,ind,tag,id)
                    execution_units[index]['cpu']['obs']=value
                    execution_units[index]['cpu']['cache_address']='Index:'+str(ind)+'Tag:'+str(tag)
                elif execution_units[index]['cpu']['instruction'] == 'R':
                    value = read_cache(index,ind,tag)
                    if value == 'CACHE MISS':
                        execution_units[index]['cpu']['obs'] = 'C.Miss.'
                        execution_units[index]['cpu']['cache_address']='Index:'+str(ind)+'Tag:'+str(tag)
                        write_before_reading(id,execution_units[index]['cpu']['address'],index,ind,tag)
                        print("Cache miss 1")
                        print(mem_bus)
                        get_bus_to_read_mem(id,execution_units[index]['cpu']['address'])
                        print("Cache miss 2")
                        value = read_mem(execution_units[index]['cpu']['address'])
                        update_cache(index,ind,tag,value)
                        reset_mem_bus()
                        release_bus()
                    else:
                        execution_units[index]['cpu']['obs'] = value
                        execution_units[index]['cpu']['cache_address']='Index:'+str(ind)+'Tag:'+str(tag)
                else:
                    execution_units[index]['cpu']['obs'] = '--'
                                                                                                                                                                
            view_modifications_list['cpus'][index] = {'ins':execution_units[index]['cpu']['instruction'],
                                                          'address':execution_units[index]['cpu']['address'],
                                                          'cache_address':execution_units[index]['cpu']['cache_address'],
                                                          'cycles':execution_units[index]['cpu']['cycles'],
                                                          'status':execution_units[index]['cpu']['status'],
                                                          'obs':execution_units[index]['cpu']['obs']}
                
            print(global_cycle)
            print(execution_units)

            execute_cpu_cycle = False

            
#### memory methods ####
def write_mem(address,data):
    global memory,view_modifications_list
    memory[address]['data']=data
    view_modifications_list['memory']={'address':address,'data':data}

def read_mem(address):
    return memory[address]['data']


#### cache methods ####
def write_cache(cache,index,tag,data):
    global execution_units,view_modifications_list
    text=''
    if execution_units[cache]['cache'][index]['tag'] != tag or not execution_units[cache]['cache'][index]['valid']:
        if execution_units[cache]['cache'][index]['tag'] != tag and execution_units[cache]['cache'][index]['valid'] and execution_units[cache]['cache'][index]['modified']:
            address = 8*execution_units[cache]['cache'][index]['tag']+index
            cpu='CPU'+str(cache+1)
            get_bus_to_write_mem(cpu,address)
            write_mem(address,cpu)
            control[cache]['obs'] = 'B.Modified'
            control[cache]['action'] = 'WBW'
            view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}
            release_bus()
        text = 'W.Miss'
    else:
        text = '--'
    execution_units[cache]['cache'][index]['valid']=1
    execution_units[cache]['cache'][index]['modified']=1
    execution_units[cache]['cache'][index]['tag']=tag
    execution_units[cache]['cache'][index]['data']=data
    control[cache]['invalidate_index']=index
    control[cache]['invalidate_tag']=tag
    update_cache_views(cache,index,('1','1',tag,data))
    return text

def read_cache(cache,index,tag):
    global execution_units
    if execution_units[cache]['cache'][index]['valid'] == 1 and execution_units[cache]['cache'][index]['tag'] == tag:
        return execution_units[cache]['cache'][index]['data']
    else:
        return 'CACHE MISS'

def update_cache(cache,index,tag,data):
    global execution_units,view_modifications_list
    execution_units[cache]['cache'][index]['valid']=1
    execution_units[cache]['cache'][index]['modified']=0
    execution_units[cache]['cache'][index]['tag']=tag
    execution_units[cache]['cache'][index]['data']=data
    update_cache_views(cache,index,('1','0',tag,data))
    return
    
#### Fetch instructions methods ####
def create_new_instruction():
    tipe = random.choice(['M','P'])
    if tipe == 'M':
        tipe = random.choice(['W','R'])
        address = random.choice(range(16))
        cycles = 4
    else:
        cycles = 3
        address = -1
    return [tipe,cycles,address]

#### bus methods ####
def get_bus_to_read_mem(cpu,address):
    global mem_bus
    
    mem_bus['cpu_in_bus'] = cpu
    mem_bus['address'] = address
    mem_bus['instruction_type'] = 'R'
    cpu_list=['CPU1','CPU2','CPU3','CPU4']
    cpu_list.remove(cpu)
    cond=True
    while cond:
        if cpu_list[0] in mem_bus['cpus_notified'] and cpu_list[1] in mem_bus['cpus_notified'] and cpu_list[2] in mem_bus['cpus_notified']:
            if mem_bus['back_off'] != '--':
                mem_bus['obs'] = 'BackOff_'+mem_bus['back_off']
            view_modifications_list['bus'] = {'cpu_in_bus':cpu,'ins':'R','address':str(address),'obs':mem_bus['obs']}
            mem_bus['mutex'].acquire()
            cond = False
            return

def get_bus_to_write_mem(cpu,address):
    global mem_bus,view_modifications_list
    mem_bus['mutex'].acquire()
    view_modifications_list['bus'] = {'cpu_in_bus':cpu,'ins':'W','address':str(address),'obs':mem_bus['obs']}
    return

def release_bus():
    mem_bus['mutex'].release()

def back_off_inst(cpu,address):
    get_bus_to_write_mem(cpu,address)
    write_mem(address,cpu)
    release_bus()
    mem_bus['back_off'] = cpu
    
def reset_mem_bus():
    mem_bus['cpu_in_bus'] = '--'
    mem_bus['instruction_type']='--'
    mem_bus['address']=-1
    mem_bus['obs']='--'
    mem_bus['cpus_notified']=[]
    mem_bus['back_off']='--'

### control cache methods ###
def write_before_reading(cpu,address,cache,index,tag):
    global execution_units,control,view_modifications_list
    if execution_units[cache]['cache'][index]['valid'] == 1 and execution_units[cache]['cache'][index]['tag'] != tag and execution_units[cache]['cache'][index]['modified'] == 1:
        get_bus_to_write_mem(cpu,address)
        write_mem(address,cpu)
        control[cache]['obs'] = 'B.Modified'
        control[cache]['action'] = 'WBR'
        view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}
        release_bus()
    return

def invalidate_cache_block(cache,index,cpu):
    global execution_units, control,view_modifications_list
    execution_units[cache]['cache'][index]['valid'] = 0
    control[cache]['obs'] = 'CPU'+str(cpu+1)
    control[cache]['action'] = 'Invalid'
    update_cache_views(cache,index,('0','0',execution_units[cache]['cache'][index]['tag'],execution_units[cache]['cache'][index]['data']))
    view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}

def reset_control(index):
    global control,view_modifications_list
    control[index]['obs'] = '--'
    control[index]['action'] = '--'
    control[index]['invalidate_index']=-1
    control[index]['invalidate_tag']=-1
    control[index]['cpus_notified']=[]
    view_modifications_list['controls'][index] = {'obs':'--','action':'--'}

#### gui update methods ####

def update_cache_views(cache,index,values):
    global view_modifications_list
    mutex_cache.acquire()
    if view_modifications_list['caches'][cache] == None:
        view_modifications_list['caches'][cache] = [{'index':index,'values':values}]
    else:
        view_modifications_list['caches'][cache].append({'index':index,'values':values})
    mutex_cache.release()

#### creation methods ####
def create_execution_units():
    global execution_units
    threads = []
    for j in range(4):
        cpu = {'id':'CPU'+str(j+1),'instruction':'','address':0,'cache_address':'','cycles':0,'status':'','obs':'--'}
        cache = []
        for i in range(8):
            cache.append({'valid':0,'modified':0,'tag':0,'data':0})
        execution_units.append({'cpu':cpu,'cache':cache})
        threads.append(threading.Thread(target=cpu_thread,args=(j,)))
    threads[0].start()
    threads[1].start()
    threads[2].start()
    threads[3].start()    

def create_control_caches():
    global control
    threads = []
    for j in range(4):
        cont_info = {'id':'CPU'+str(j+1),'obs':'--','action':'--','invalidate_index':-1,'invalidate_tag':-1,'cpus_notified':[]}
        control.append(cont_info)
        threads.append(threading.Thread(target=control_thread,args=(j,)))
    threads[0].start()
    threads[1].start()
    threads[2].start()
    threads[3].start()

def create_clock():
    while True:
        global execute_cpu_cycle,cycle_time,global_cycle
        execute_cpu_cycle = True
        global_cycle += 1
        view_modifications_list['clock'] = global_cycle
        time.sleep(cycle_time)
        
def create_mem_bus():
    global mem_bus
    mem_bus = {'cpu_in_bus':'--','mutex': threading.Lock(),'instruction_type':'--','address':-1,'obs':'--','cpus_notified':[],'back_off':'--'}

def create_mem():
    global mem
    for i in range(16):
        memory.append({'data':0})

def create_all_views():
    global root,cache_views,control_views, cpu_views,memory_view,bus_view,clock_view
    for i in range(4):
        lbl = Label(root, text="CPU "+str(i+1))
        lbl.place(x=250 * i + 10,y=10)
        tv = Treeview(root,height = 6)
        tv['columns'] = ('value')
        tv.heading("#0", text='Descrip.')
        tv.column("#0",width=75)
        tv.heading('value', text='Value')
        tv.column('value', anchor='center', width=145)
        tv.grid(sticky = (N,S,W,E))
        tv.place(x= 250 * i + 7, y = 35)
        cpu_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        cpu_views[i].insert('', 'end','ins', text='Inst.', values=('--'))
        cpu_views[i].insert('', 'end','address', text='Address', values=('--'))
        cpu_views[i].insert('', 'end','cache_address', text='Cache', values=('--'))
        cpu_views[i].insert('', 'end','cycles', text='Cycles', values=('--'))
        cpu_views[i].insert('', 'end','status', text='Status', values=('--'))
        cpu_views[i].insert('', 'end','obs', text='Obs.', values=('--'))
        
    for i in range(4):
        lbl = Label(root, text="Cache "+str(i+1))
        lbl.place(x=250 * i + 10,y=185)
        tv = Treeview(root,height = 8)
        tv['columns'] = ('valid','modified', 'tag', 'data')
        tv.heading("#0", text='Index')
        tv.column("#0", anchor="center",width=45)
        tv.heading('valid', text='V')
        tv.column('valid', anchor='center', width=30)
        tv.heading('modified', text='M')
        tv.column('modified', anchor='center', width=30)
        tv.heading('tag', text='Tag')
        tv.column('tag', anchor='center', width=45)
        tv.heading('data', text='Data')
        tv.column('data', anchor='center', width=60)
        tv.grid(sticky = (N,S,W,E))
        tv.place(x= 250 * i + 7, y = 210)
        cache_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        for j in range(8):
            cache_views[i].insert('', 'end','block'+str(j), text=str(j), values=('0','0','0','0'))

    for i in range(4):
        lbl = Label(root, text="Control "+str(i+1))
        lbl.place(x=250 * i + 10,y=400)
        tv = Treeview(root,height = 2)
        tv['columns'] = ('value')
        tv.heading("#0", text='Descrip.')
        tv.column("#0",width=65)
        tv.heading('value', text='Value')
        tv.column('value', anchor='center', width=145)
        tv.grid(sticky = (N,S,W,E))
        tv.place(x= 250 * i + 7, y = 425)
        control_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        control_views[i].insert('', 'end','obs', text='Obs.', values=('---'))
        control_views[i].insert('', 'end','action', text='Action', values=('---'))
        
    lbl = Label(root, text="Clock")
    lbl.place(x=1003,y=10)
    tv = Treeview(root,height = 2)
    tv['columns'] = ('value')
    tv.heading("#0", text='Descrip.')
    tv.column("#0", anchor="center",width=70)
    tv.heading('value', text='Value')
    tv.column('value', anchor='center', width=60)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 1000, y = 35)
    clock_view = tv #Append solo en la creacion, sustituir en actualizacion
    clock_view.insert('', 'end','time', text='C. Time', values=(str(cycle_time)))
    clock_view.insert('', 'end','cycle', text='Cycle', values=('0'))
    
    lbl = Label(root, text="Bus")
    lbl.place(x=263,y=500)
    tv = Treeview(root,height = 1)
    tv['columns'] = ('ins','address')
    tv.heading("#0", text='Control in bus')
    tv.column("#0", anchor="center",width=150)
    tv.heading('ins', text='Instruction')
    tv.column('ins', anchor='center', width=150)
    tv.heading('address', text='Address')
    tv.column('address', anchor='center', width=150)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 260, y = 525)
    bus_view = tv #Append solo en la creacion, sustituir en actualizacion
    bus_view.insert('', 'end','bus', text='--', values=('--','--'))

    lbl = Label(root, text="Memory")
    lbl.place(x=1003,y=145)
    tv = Treeview(root,height = 16)
    width_all=65
    tv['columns'] = ('data')
    tv.heading("#0", text='Address')
    tv.column("#0", anchor="center",width=width_all)
    tv.heading('data', text='Data')
    tv.column('data', anchor='center', width=width_all)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 1000, y = 170)
    memory_view = tv #Append solo en la creacion, sustituir en actualizacion
    for j in range(16):
        memory_view.insert('', 'end','block'+str(j), text=str(j), values=('0'))
    root.after(100, update_all_views)

def update_all_views():
    global view_modifications_list
    
    #clock_view update
    if view_modifications_list['clock'] != None:
        clock_view.item('cycle', values=(str(view_modifications_list['clock'])))
        view_modifications_list['clock'] = None

    #cpus_view update
    for i in range(4):
        if view_modifications_list['cpus'][i] != None:
            if view_modifications_list['cpus'][i]['ins']!='P':
                cpu_views[i].item('address', values=(str(view_modifications_list['cpus'][i]['address'])))
                cpu_views[i].item('cache_address', values=(str(view_modifications_list['cpus'][i]['cache_address'])))
            else:
                cpu_views[i].item('address', values=('--'))
                cpu_views[i].item('cache_address', values=('--'))
            cpu_views[i].item('ins', values=(view_modifications_list['cpus'][i]['ins']))            
            cpu_views[i].item('cycles', values=(str(view_modifications_list['cpus'][i]['cycles'])))
            cpu_views[i].item('status', values=(str(view_modifications_list['cpus'][i]['status'])))
            cpu_views[i].item('obs', values=(str(view_modifications_list['cpus'][i]['obs'])))
            view_modifications_list['cpus'][i]=None

    #cache_views update                      
    for i in range(4):
        mutex_cache.acquire()
        if view_modifications_list['caches'][i] != None:
            for change in view_modifications_list['caches'][i]:
                #cache_views[i].item('block'+str(view_modifications_list['caches'][i]['index']),values=view_modifications_list['caches'][i]['values'])
                cache_views[i].item('block'+str(change['index']),values=change['values'])
            view_modifications_list['caches'][i] = None
        mutex_cache.release()
            
    #control_views update                      
    for i in range(4):
        if view_modifications_list['controls'][i] != None:
            control_views[i].item('obs',values=view_modifications_list['controls'][i]['obs'])
            control_views[i].item('action',values=view_modifications_list['controls'][i]['action'])
            view_modifications_list['controls'][i] = None

    #memory_view update
    if view_modifications_list['memory'] != None:
        memory_view.item('block'+str(view_modifications_list['memory']['address']),values=(view_modifications_list['memory']['data']))
        view_modifications_list['memory'] = None
                         
    root.after(100, update_all_views)

def main():
    create_execution_units()
    create_mem()
    create_mem_bus()
    create_control_caches()
    #dejar clock de ultimo
    threading.Thread(target=create_clock).start()
    
    create_all_views()
main()
