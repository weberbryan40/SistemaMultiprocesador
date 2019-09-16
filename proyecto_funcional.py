try:
    from Tkinter import *
    from ttk import *
except ImportError:  # Python 3
    from tkinter import *
    from tkinter.ttk import *
import threading
import time
import queue
import random
import numpy as np
from sys import stdout


#variables for logical part
cycle_time = 4
global_cycle = 0
execute_cpu_cycle = [False,False,False,False]
execution_units = []
memory = []
control = []
scales_inst_values=[]
scales_mem_values=[]
broadcast = None
mem_bus = None

mutex_broadcast = threading.Lock()
mutex_cache = threading.Lock()
mutex_bus = threading.Lock()
mutex_bus_mutex = threading.Lock()

#variables for graphic part
cache_views=[]
control_views=[]
cpu_views=[]
scales_inst=[]
scales_inst_labels=[]
scales_mem=[]
scales_mem_labels=[]
scales_time=None
scale_time_value=4
scale_time_label=None
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
root.geometry("1150x670")

#Broadcast Thread
def broadcast_thread():
    global broadcast

    while True:
        next_request = broadcast['queue'].get()
        broadcast['request'] = next_request['request']
        broadcast['cpu_owner'] = next_request['cpu_owner']
        while len(broadcast['cpus_notified']) < 3:
            print(len(broadcast['cpus_notified']))
            pass
        reset_broadcast()
                

#Hilo para controlador
def control_thread(cache):
    global execute_cpu_cycle,execution_units,mem_bus,view_modifications_list,global_cycle,control,control,broadcast, mutex_broadcast
    cpu_list=[0,1,2,3]
    cpu_list.remove(cache)
    
    while True:

        #mutex_broadcast.acquire()
        if broadcast['request'] != None:
            index=broadcast['request']['index']
            tag=broadcast['request']['tag']
            if broadcast['request']['type'] == 'W' and broadcast['cpu_owner'] != cache:
                if execution_units[cache]['cache'][index]['tag'] == tag and execution_units[cache]['cache'][index]['valid']==1:
                    invalidate_cache_block(cache,index,broadcast['cpu_owner'])
                if cache not in broadcast['cpus_notified']:
                    broadcast['cpus_notified'].append(cache)
                
        #mutex_broadcast.release()
            elif broadcast['request']['type'] == 'R' and broadcast['cpu_owner'] != cache:
                if execution_units[cache]['cache'][index]['valid'] == 1 and \
                   execution_units[cache]['cache'][index]['tag'] == tag and \
                   execution_units[cache]['cache'][index]['modified'] == 1:
                    
                    #
                    control[broadcast['cpu_owner']]['index_read'] = index
                    control[broadcast['cpu_owner']]['tag_read'] = tag
                    control[broadcast['cpu_owner']]['data_read'] = execution_units[cache]['cache'][index]['data']
                    #control[broadcast['cpu_owner']]['read_now'] = True

                    execution_units[broadcast['cpu_owner']]['cpu']['status'] = 'WaitWB'
                    view_modifications_list['cpus'][broadcast['cpu_owner']] = {'ins':execution_units[broadcast['cpu_owner']]['cpu']['instruction'],
                                                  'address':execution_units[broadcast['cpu_owner']]['cpu']['address'],
                                                  'cache_address':execution_units[broadcast['cpu_owner']]['cpu']['cache_address'],
                                                  'cycles':execution_units[broadcast['cpu_owner']]['cpu']['cycles'],
                                                  'status':execution_units[broadcast['cpu_owner']]['cpu']['status'],
                                                  'obs':execution_units[broadcast['cpu_owner']]['cpu']['obs']}
                    
                    write_back(cache,8*tag+index)                    
                    
                    print(mem_bus['cpu_in_bus'])

                elif execution_units[cache]['cache'][index]['valid'] == 1 and \
                   execution_units[cache]['cache'][index]['tag'] == tag and \
                   execution_units[cache]['cache'][index]['modified'] == 0:
                    
                    #
                    control[broadcast['cpu_owner']]['index_read'] = index
                    control[broadcast['cpu_owner']]['tag_read'] = tag
                    control[broadcast['cpu_owner']]['data_read'] = execution_units[cache]['cache'][index]['data']

                    migration(cache,8*tag+index)            
                    
                if not cache in broadcast['cpus_notified']:
                    if len(broadcast['cpus_notified'])+1 == 3: # se hace para que se tome el valor correcto en broadcast['cpu_owner'] antes de hacer reset del broadcast
                        control[broadcast['cpu_owner']]['read_now'] = True
                    broadcast['cpus_notified'].append(cache)
                        
        
        time.sleep(0.1)

#Hilo para CPUs
def cpu_thread(index):
    global execute_cpu_cycle,execution_units,mem_bus,view_modifications_list,global_cycle,broadcast
    id = execution_units[index]['cpu']['id']
    cpu_list=[0,1,2,3]
    cpu_list.remove(index)
    while True: 
        if execute_cpu_cycle[index]:
            execution_units[index]['cpu']['cycles'] -= 1
        
            if execution_units[index]['cpu']['cycles'] <= 0:
                ##OJO: RECORDAR PONER EL STATUS DEL CPU
                execution_units[index]['cpu']['instruction'],execution_units[index]['cpu']['cycles'],execution_units[index]['cpu']['address'] = create_new_instruction(index)
                execution_units[index]['cpu']['status'] = 'Running'#POR AHORA
                reset_control(index)
                print(index)
                tag=execution_units[index]['cpu']['address']//8
                ind=execution_units[index]['cpu']['address']%8
                execution_units[index]['cpu']['cache_address']='Index:'+str(ind)+'Tag:'+str(tag)
                view_modifications_list['cpus'][index] = {'ins':execution_units[index]['cpu']['instruction'],
                                                          'address':execution_units[index]['cpu']['address'],
                                                          'cache_address':execution_units[index]['cpu']['cache_address'],
                                                          'cycles':execution_units[index]['cpu']['cycles'],
                                                          'status':execution_units[index]['cpu']['status'],
                                                          'obs':execution_units[index]['cpu']['obs']}
                if execution_units[index]['cpu']['instruction'] == 'W':
                    mutex_broadcast.acquire()
                    insert_request({'type':'W','index':ind,'tag':tag},index)
                    mutex_broadcast.release()
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
                        ###
                        mutex_broadcast.acquire()
                        insert_request({'type':'R','index':ind,'tag':tag},index)
                        mutex_broadcast.release()
                        execution_units[index]['cpu']['status'] = 'InBroadcast'
                        view_modifications_list['cpus'][index] = {'ins':execution_units[index]['cpu']['instruction'],
                                                      'address':execution_units[index]['cpu']['address'],
                                                      'cache_address':execution_units[index]['cpu']['cache_address'],
                                                      'cycles':execution_units[index]['cpu']['cycles'],
                                                      'status':execution_units[index]['cpu']['status'],
                                                      'obs':execution_units[index]['cpu']['obs']}
                        while not control[index]['read_now']:
                            pass
                        if control[index]['data_read'] == '':                            
                            get_bus_to_read_mem(index,id,execution_units[index]['cpu']['address'])
                            execution_units[index]['cpu']['status'] = 'Blocked'
                            view_modifications_list['cpus'][index] = {'ins':execution_units[index]['cpu']['instruction'],
                                                          'address':execution_units[index]['cpu']['address'],
                                                          'cache_address':execution_units[index]['cpu']['cache_address'],
                                                          'cycles':execution_units[index]['cpu']['cycles'],
                                                          'status':execution_units[index]['cpu']['status'],
                                                          'obs':execution_units[index]['cpu']['obs']}
                            print("Cache miss 2")
                            value = read_mem(execution_units[index]['cpu']['address'])
                            update_cache(index,ind,tag,value)
                            control[index]['obs'] = 'C.Miss'
                            control[index]['action'] = 'R.MEM'
                            view_modifications_list['controls'][index] = {'obs':control[index]['obs'],'action':control[index]['action']}
                            while mem_bus['cycles'] > 0:
                                pass
                            reset_mem_bus()
                            release_bus()
                            execution_units[index]['cpu']['status'] = 'Running'                            
                        else:
                            execution_units[index]['cpu']['status'] = 'Running'   
                            update_cache(index,ind,tag,control[index]['data_read'])
                        reset_control_reads(index)
                    else:
                        execution_units[index]['cpu']['obs'] = value
                        execution_units[index]['cpu']['cache_address']='Index:'+str(ind)+'Tag:'+str(tag)
                else:
                    execution_units[index]['cpu']['obs'] = '--'
            execution_units[index]['cpu']['status'] = 'Running'                                                                                                                     
            view_modifications_list['cpus'][index] = {'ins':execution_units[index]['cpu']['instruction'],
                                                          'address':execution_units[index]['cpu']['address'],
                                                          'cache_address':execution_units[index]['cpu']['cache_address'],
                                                          'cycles':execution_units[index]['cpu']['cycles'],
                                                          'status':execution_units[index]['cpu']['status'],
                                                          'obs':execution_units[index]['cpu']['obs']}
                
            print(global_cycle)
            print(execution_units[1])

            execute_cpu_cycle[index] = False

            
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
            control[cache]['obs'] = 'B.Modified'
            control[cache]['action'] = 'WBW'
            view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}
            execution_units[cache]['cpu']['status'] = 'Blocked'
            view_modifications_list['cpus'][cache] = {'ins':execution_units[cache]['cpu']['instruction'],
                                          'address':execution_units[cache]['cpu']['address'],
                                          'cache_address':execution_units[cache]['cpu']['cache_address'],
                                          'cycles':execution_units[cache]['cpu']['cycles'],
                                          'status':execution_units[cache]['cpu']['status'],
                                          'obs':execution_units[cache]['cpu']['obs']}
            write_mem(address,cpu)
            control[cache]['obs'] = 'B.Modified'
            control[cache]['action'] = 'WBW'
            view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}
            while mem_bus['cycles'] > 0:
                pass
            reset_mem_bus()
            release_bus()
            execution_units[cache]['cpu']['status'] = 'Running'   
        text = 'W.Miss'
    else:
        text = '--'
    execution_units[cache]['cache'][index]['valid']=1
    execution_units[cache]['cache'][index]['modified']=1
    execution_units[cache]['cache'][index]['tag']=tag
    execution_units[cache]['cache'][index]['data']=data
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

def invalidate_cache_block(cache,index,cpu):
    global execution_units, control,view_modifications_list
    execution_units[cache]['cache'][index]['valid'] = 0
    control[cache]['invalid'] = 'Index:'+str(index)
    control[cache]['by_cpu'] = 'CPU'+str(cpu+1)
    update_cache_views(cache,index,('0','0',execution_units[cache]['cache'][index]['tag'],execution_units[cache]['cache'][index]['data']))
    view_modifications_list['controls'][cache] = {'invalid':control[cache]['invalid'],'by_cpu':control[cache]['by_cpu']}

#### Fetch instructions methods ####
def create_new_instruction(cpu):
    global scales_inst,scales_mem
    tipe=random.choice([0,1])
    if(len(scales_inst)==4):
        tipe = np.random.binomial(1, scales_inst_values[cpu]/100, 100)[49]
    if tipe == 1:
        tipe=random.choice([0,1])
        if(len(scales_mem)==4):
            tipe = np.random.binomial(1, scales_mem_values[cpu]/100, 100)[49]
        #tipe = random.choice(['W','R'])
        if tipe == 1:
            tipe = 'R'
        else:
            tipe = 'W'
        address = random.choice(range(16))
        cycles = 2
    else:
        tipe='P'
        cycles = 2
        address = -1
    return [tipe,cycles,address]

#### bus methods ####
def get_bus_to_read_mem(id,cpu,address):
    global mem_bus    
    
    cpu_list=['CPU1','CPU2','CPU3','CPU4']
    cpu_list.remove(cpu)
    if mem_bus['back_off'] != '--':
        mem_bus['obs'] = 'BackOff_'+mem_bus['back_off']
    
    if mem_bus['mutex'].locked():
        execution_units[id]['cpu']['status'] = 'WaitingBus'
    else:
        execution_units[id]['cpu']['status'] = 'Blocked'
    view_modifications_list['cpus'][id] = {'ins':execution_units[id]['cpu']['instruction'],
                                          'address':execution_units[id]['cpu']['address'],
                                          'cache_address':execution_units[id]['cpu']['cache_address'],
                                          'cycles':execution_units[id]['cpu']['cycles'],
                                          'status':execution_units[id]['cpu']['status'],
                                          'obs':execution_units[id]['cpu']['obs']}
    mem_bus['mutex'].acquire()
    mem_bus['cpu_in_bus'] = cpu
    mem_bus['address'] = address
    mem_bus['instruction_type'] = 'R'
    mem_bus['cycles']=3
    mutex_bus.acquire()
    view_modifications_list['bus'] = {'cpu_in_bus':cpu,'values':('R',str(address),3)}
    mutex_bus.release()
    
    return

def get_bus_to_write_mem(cpu,address):
    global mem_bus,view_modifications_list
    id=int(cpu[3])-1
    if mem_bus['mutex'].locked():
        execution_units[id]['cpu']['status'] = 'WaitingBus'
    else:
        execution_units[id]['cpu']['status'] = 'Blocked'
    view_modifications_list['cpus'][id] = {'ins':execution_units[id]['cpu']['instruction'],
                                          'address':execution_units[id]['cpu']['address'],
                                          'cache_address':execution_units[id]['cpu']['cache_address'],
                                          'cycles':execution_units[id]['cpu']['cycles'],
                                          'status':execution_units[id]['cpu']['status'],
                                          'obs':execution_units[id]['cpu']['obs']}
    mem_bus['mutex'].acquire()
    mem_bus['cpu_in_bus'] = cpu
    mem_bus['address'] = address
    mem_bus['instruction_type'] = 'W'
    mem_bus['cycles']=3
    mutex_bus.acquire()
    view_modifications_list['bus'] = {'cpu_in_bus':cpu,'values':('W',str(address),str(3))}
    mutex_bus.release()
    return

def release_bus():
    global mem_bus
    mem_bus['cycles']=0
    mem_bus['mutex'].release()

def write_back(id,address):
    cpu='CPU'+str(id+1)
    index=address%8
    tag=address//8
    get_bus_to_write_mem(cpu,address)
    write_mem(address,cpu)
    mem_bus['back_off'] = cpu
    update_cache(id,index,tag,execution_units[id]['cache'][index]['data'])#para cambiar el estado a compartido
    k = broadcast['cpu_owner']
    control[k]['obs'] = cpu
    control[k]['action'] = 'WriteBack'
    view_modifications_list['controls'][k] = {'obs':control[k]['obs'],'action':control[k]['action']}
    while mem_bus['cycles'] > 0:
        pass
    reset_mem_bus()
    release_bus()

def migration(id,address):
    cpu='CPU'+str(id+1)
    index=address%8
    tag=address//8
    k = broadcast['cpu_owner']
    control[k]['obs'] = cpu
    control[k]['action'] = 'Migrating'
    view_modifications_list['controls'][k] = {'obs':control[k]['obs'],'action':control[k]['action']}
    
def reset_mem_bus():
    mem_bus['cpu_in_bus'] = '--'
    mem_bus['instruction_type']='--'
    mem_bus['address']=-1
    mem_bus['obs']='--'
    mem_bus['cpus_notified']=[]
    mem_bus['back_off']='--'
    mem_bus['cycles']=0
    mutex_bus.acquire()
    view_modifications_list['bus'] = {'cpu_in_bus':'--','values':('--','--','--')}
    mutex_bus.release()

### control cache methods ###
def write_before_reading(cpu,address,cache,index,tag):
    global execution_units,control,view_modifications_list
    if execution_units[cache]['cache'][index]['valid'] == 1 and execution_units[cache]['cache'][index]['tag'] != tag and execution_units[cache]['cache'][index]['modified'] == 1:
        get_bus_to_write_mem(cpu,8*execution_units[cache]['cache'][index]['tag']+index)
        write_mem(8*execution_units[cache]['cache'][index]['tag']+index,cpu)
        control[cache]['obs'] = 'B.Modified'
        control[cache]['action'] = 'WBR'
        view_modifications_list['controls'][cache] = {'obs':control[cache]['obs'],'action':control[cache]['action']}
        reset_mem_bus()
        release_bus()
    return

def reset_control(index):
    global control,view_modifications_list
    control[index]['obs'] = '--'
    control[index]['action'] = '--'
    control[index]['invalid'] = '--'
    control[index]['by_cpu'] = '--'
    view_modifications_list['controls'][index] = {'obs':'--','action':'--','invalid':'--','by_cpu':'--'}

def reset_control_reads(index):
    global control
    control[index]['index_read']=-1
    control[index]['tag_read']=-1
    control[index]['data_read']=''
    control[index]['read_now']=False
#### broadcast methods ####

def insert_request(request,cpu):
    global broadcast,view_modifications_list
    broadcast['queue'].put({'request':request,'cpu_owner':cpu})

def reset_broadcast():
    global broadcast
    broadcast['request']=None
    broadcast['cpus_notified']=[]
    broadcast['cpu_owner']=-1
    broadcast['cache_data']=None

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
        cont_info = {'id':'CPU'+str(j+1),'obs':'--','action':'--','invalid':'--','by_cpu':'--','read_now':False,'index_read':-1,'tag_read':-1,'data_read':''}
        control.append(cont_info)
        threads.append(threading.Thread(target=control_thread,args=(j,)))
    threads[0].start()
    threads[1].start()
    threads[2].start()
    threads[3].start()

def create_broadcast():
    global broadcast
    broadcast = {'queue':queue.Queue(),'cpus_notified':[],'cpu_owner':-1,'request':None}
    threading.Thread(target=broadcast_thread).start()
def create_clock():
    global execute_cpu_cycle,cycle_time,global_cycle
    while True:        
        execute_cpu_cycle = [True,True,True,True]
        global_cycle += 1
        view_modifications_list['clock'] = global_cycle
        time.sleep(cycle_time)
        if mem_bus['mutex'].locked():
            mem_bus['cycles']-=1
            mutex_bus.acquire()
            view_modifications_list['bus'] = {'cpu_in_bus':mem_bus['cpu_in_bus'],'values':(mem_bus['instruction_type'],mem_bus['address'],str(mem_bus['cycles']))}
            mutex_bus.release()
        
def create_mem_bus():
    global mem_bus
    mem_bus = {'cpu_in_bus':'--','mutex': threading.Lock(),'instruction_type':'--','address':-1,'obs':'--','cpus_notified':[],'back_off':'--','cycles':0}

def create_mem():
    global mem
    for i in range(16):
        memory.append({'data':0})

def create_all_views():
    global root,cache_views,control_views, cpu_views,memory_view,bus_view,clock_view,scales_inst,scales_mem,scales_inst_labels,scales_mem_labels, scales_inst_values,scales_mem_values,scale_time_label,scale_time,scale_time_value
    for i in range(4):
        label = Label(root)
        label.config(text = 'Mem. Ins.')
        label.place(x=250 * i + 10, y=10)
        scale = Scale( root, orient = HORIZONTAL,from_=0,to=100)
        scale.set(50)
        scale.place(x=250 * i + 87, y = 10)
        scales_inst.append(scale)
        scales_inst_values.append(int(scale.get()))
        label = Label(root)
        label.config(text =  str(int(scale.get()))+' %')
        label.place(x=250 * i + 195, y=10)      
        scales_inst_labels.append(label)

        label = Label(root)
        label.config(text = 'R. Mem.')
        label.place(x=250 * i + 10, y=35)
        scale = Scale( root, orient = HORIZONTAL,from_=0,to=100)
        scale.set(50)
        scale.place(x=250 * i + 87, y = 35)
        scales_mem.append(scale)
        scales_mem_values.append(int(scale.get()))
        label = Label(root)
        label.config(text =  str(int(scale.get()))+' %')
        label.place(x=250 * i + 195, y=35)      
        scales_mem_labels.append(label)
    
    for i in range(4):
        lbl = Label(root, text="CPU "+str(i+1))
        lbl.place(x=250 * i + 10,y=60)
        tv = Treeview(root,height = 6)
        tv['columns'] = ('value')
        tv.heading("#0", text='Descrip.')
        tv.column("#0",width=75)
        tv.heading('value', text='Value')
        tv.column('value', anchor='center', width=145)
        tv.grid(sticky = (N,S,W,E))
        tv.place(x= 250 * i + 7, y = 85)
        cpu_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        cpu_views[i].insert('', 'end','ins', text='Inst.', values=('--'))
        cpu_views[i].insert('', 'end','address', text='Address', values=('--'))
        cpu_views[i].insert('', 'end','cache_address', text='Cache', values=('--'))
        cpu_views[i].insert('', 'end','cycles', text='Cycles', values=('--'))
        cpu_views[i].insert('', 'end','status', text='Status', values=('--'))
        cpu_views[i].insert('', 'end','obs', text='Obs.', values=('--'))
        
    for i in range(4):
        lbl = Label(root, text="Cache "+str(i+1))
        lbl.place(x=250 * i + 10,y=235)
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
        tv.place(x= 250 * i + 7, y = 260)
        cache_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        for j in range(8):
            cache_views[i].insert('', 'end','block'+str(j), text=str(j), values=('0','0','0','0'))

    for i in range(4):
        lbl = Label(root, text="Control "+str(i+1))
        lbl.place(x=250 * i + 10,y=450)
        tv = Treeview(root,height = 4)
        tv['columns'] = ('value')
        tv.heading("#0", text='Descrip.')
        tv.column("#0",width=65)
        tv.heading('value', text='Value')
        tv.column('value', anchor='center', width=145)
        tv.grid(sticky = (N,S,W,E))
        tv.place(x= 250 * i + 7, y = 475)
        control_views.append(tv) #Append solo en la creacion, sustituir en actualizacion
        control_views[i].insert('', 'end','obs', text='Obs.', values=('--'))
        control_views[i].insert('', 'end','action', text='Action', values=('--'))
        control_views[i].insert('', 'end','invalid', text='Invalid', values=('--'))
        control_views[i].insert('', 'end','by_cpu', text='By', values=('--'))

    label = Label(root)
    label.config(text = 'Cycle Time')
    label.place(x=1003, y=10)
    scale = Scale( root, orient = HORIZONTAL,from_=1,to=10)
    scale.set(4)
    scale.place(x=1003, y = 35)
    scale_time = scale
    scale_time_value=int(scale.get())
    label = Label(root)
    label.config(text =  str(int(scale.get()))+' s')
    label.place(x=1110, y=35)      
    scale_time_label=label
    
    lbl = Label(root, text="Clock")
    lbl.place(x=1003,y=60)
    tv = Treeview(root,height = 2)
    tv['columns'] = ('value')
    tv.heading("#0", text='Descrip.')
    tv.column("#0", anchor="center",width=70)
    tv.heading('value', text='Value')
    tv.column('value', anchor='center', width=60)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 1000, y = 85)
    clock_view = tv #Append solo en la creacion, sustituir en actualizacion
    clock_view.insert('', 'end','time', text='C. Time', values=(str(cycle_time)))
    clock_view.insert('', 'end','cycle', text='Cycle', values=('0'))
    
    lbl = Label(root, text="Bus")
    lbl.place(x=263,y=585)
    tv = Treeview(root,height = 1)
    tv['columns'] = ('ins','address','cycles')
    tv.heading("#0", text='Control in bus')
    tv.column("#0", anchor="center",width=150)
    tv.heading('ins', text='Instruction')
    tv.column('ins', anchor='center', width=150)
    tv.heading('address', text='Address')
    tv.column('address', anchor='center', width=150)
    tv.heading('cycles', text='Cycles')
    tv.column('cycles', anchor='center', width=150)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 260, y = 610)
    bus_view = tv #Append solo en la creacion, sustituir en actualizacion
    bus_view.insert('', 'end','bus', text='--', values=('--','--','--'))

    lbl = Label(root, text="Memory")
    lbl.place(x=1003,y=200)
    tv = Treeview(root,height = 16)
    width_all=65
    tv['columns'] = ('data')
    tv.heading("#0", text='Address')
    tv.column("#0", anchor="center",width=width_all)
    tv.heading('data', text='Data')
    tv.column('data', anchor='center', width=width_all)
    tv.grid(sticky = (N,S,W,E))
    tv.place(x= 1000, y = 225)
    memory_view = tv #Append solo en la creacion, sustituir en actualizacion
    for j in range(16):
        memory_view.insert('', 'end','block'+str(j), text=str(j), values=('0'))
    root.after(100, update_all_views)

def update_all_views():
    global cycle_time,view_modifications_list,scales_inst,scales_inst_labels,scales_mem,scales_mem_labels,scales_inst_values,scales_mem_values,scale_time_label,scale_time,scale_time_value

    for i in range(4):
        scales_inst_labels[i].config(text =  str(int(scales_inst[i].get()))+' %')
        scales_mem_labels[i].config(text =  str(int(scales_mem[i].get()))+' %')
        scales_inst_values[i]=int(scales_inst[i].get())
        scales_mem_values[i]=int(scales_mem[i].get())

    if scale_time_label != None and  scale_time != None:
        scale_time_label.config(text =  str(int(scale_time.get()))+' s')
        scale_time_value=int(scale_time.get())
        cycle_time = scale_time_value
        clock_view.item('time', values=(str(cycle_time)))
        
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
            if 'obs' in view_modifications_list['controls'][i]:
                control_views[i].item('obs',values=view_modifications_list['controls'][i]['obs'])
                control_views[i].item('action',values=view_modifications_list['controls'][i]['action'])
            if 'invalid' in view_modifications_list['controls'][i]:
                control_views[i].item('invalid',values=view_modifications_list['controls'][i]['invalid'])
                control_views[i].item('by_cpu',values=view_modifications_list['controls'][i]['by_cpu'])
            view_modifications_list['controls'][i] = None

    #bus_view update
    mutex_bus.acquire()
    if view_modifications_list['bus'] != None:
        bus_view.item('bus',text=view_modifications_list['bus']['cpu_in_bus'], values=view_modifications_list['bus']['values'])
        view_modifications_list['bus'] = None
    mutex_bus.release()
    
    #memory_view update
    if view_modifications_list['memory'] != None:
        memory_view.item('block'+str(view_modifications_list['memory']['address']),values=(view_modifications_list['memory']['data']))
        view_modifications_list['memory'] = None
                         
    root.after(100, update_all_views)

def main():
    create_broadcast()
    create_execution_units()
    create_mem()
    create_mem_bus()
    create_control_caches()
    #dejar clock de ultimo
    threading.Thread(target=create_clock).start()
    
    create_all_views()
main()
