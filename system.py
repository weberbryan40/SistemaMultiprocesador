import threading
from cpu import *
from mem_bus import *
from cache import *

class System:    
    
    def __init__(self,id):
        self.id = id
        self.memory_bus = Memory_bus(1)
        self.cache1 = Cache('CPU1')
        self.cache2 = Cache('CPU2')
        self.cache3 = Cache('CPU3')
        self.cache4 = Cache('CPU4')
        self.cpus=[CPU('CPU1',self.memory_bus,[self.cache1,[self.cache2,self.cache3,self.cache4]]),
                   CPU('CPU2',self.memory_bus,[self.cache2,[self.cache1,self.cache3,self.cache4]]),
                   CPU('CPU3',self.memory_bus,[self.cache3,[self.cache1,self.cache2,self.cache4]]),
                   CPU('CPU4',self.memory_bus,[self.cache4,[self.cache1,self.cache2,self.cache3]])]        
        return

    def notify(self):
        for cpu in self.cpus:
            cpu.new_cycle()
        return
