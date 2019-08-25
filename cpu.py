import threading
import time

class CPU:
    def thread_function(self):
        #Se hacen pausas (ciclo de reloj) y se mandan a llamar metodos de los 4 procesadores
        while True:
            print("Ejecuto")
            time.sleep(3)
    
    def __init__(self,id):
        self.id = id
        self.thread = threading.Thread(target=self.thread_function).start()
        return

    def saludar(self):
        print("Aquí cpu")
        print(str(self.id))
    
