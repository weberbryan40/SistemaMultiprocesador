import threading
import time
from sys import stdout
from instruction_fetch import *
from control_cache import *

class CPU:
    def thread_function(self):
        #Se hacen pausas (ciclo de reloj) y se mandan a llamar metodos de los 4 procesadores
        while True:
            if(self.execute):
                if  (self.instruction == 'W' or self.instruction == 'R') and  self.memory_bus.get_cpu_in_bus() == self.id:
                    self.ins_cycles -= 1

                if self.ins_cycles <= 0:
                    if self.instruction == 'W' or self.instruction == 'R':
                        self.memory_bus.release_bus()
                        #stdout.write(self.id + " libera el mutex ")
                        #stdout.write('\n')
                    self.instruction,self.cycles,self.address = self.fetch.create_new_instruction()
                    if self.instruction == 'W':
                        #stdout.write(self.id + " toma instruccion de " + self.instruction + " en la posicion " + str(self.address) + ". Duracion: " + str(self.cycles))
                        #stdout.write('\n')
                        self.cache.write_data(self.address%8,self.address//8,self.id)
                        self.control_cache.write_data_mem(self.address,self.id)
                    elif self.instruction == 'R':
                        value = self.cache.read_data(self.address%8,self.address//8)
                        if value == 'CACHE MISS':
                            #stdout.write(self.id + " tuvo un caché miss en una instrucción " + self.instruction + " en la posicion " + str(self.address))
                            self.control_cache.update_data(self.address)
                    else:
                        #stdout.write(self.id + " toma instruccion de " + self.instruction + " . Duracion: " + str(self.cycles))
                        stdout.write('')
                self.execute=False
    
    def __init__(self,id,mem_bus,caches):
        self.id = id
        self.instruction = ''
        self.ins_cycles = 0    
        self.fetch = Instruction_fetch(self.id) 
        self.memory_bus = mem_bus
        self.execute = False
        self.thread = threading.Thread(target=self.thread_function).start()
        self.cache = caches[0]
        self.control_cache = Control_cache(self.id,self.memory_bus,self.cache,caches[1])
        return

    def new_cycle(self):
        self.execute=True
