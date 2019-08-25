import threading
import time

class Clock:
    def thread_function(self):
        #Se hacen pausas (ciclo de reloj) y se mandan a llamar metodos de los 4 procesadores
        while True:
            for cpu in self.cpus:
                cpu.saludar()
            time.sleep(1)
    
    def __init__(self,id,cpus):
        self.id = id
        self.cpus = cpus
        self.thread = threading.Thread(target=self.thread_function)

    def initialize_clock(self):
        #Se crea y ejecuta el hilo ejecuta el hilo
        self.thread.start()
        return
    

    
        
