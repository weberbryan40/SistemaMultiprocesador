import threading
import time
import matplotlib.pyplot as plt
import numpy as np
from system import *

class Clock:
    def thread_function(self):
        #Se hacen pausas (ciclo de reloj) y se mandan a llamar metodos de los 4 procesadores
        while True:
            if(self.value):
                self.system.notify()
                if self.color == 'skyblue':
                    self.color = 'lightgreen'
                else:
                    self.color = 'skyblue'
            else:
                #print(self.cycle)
                self.cycle+=1
                self.mark_cycle=True
            time.sleep(self.period/2)
            self.value = not self.value

    def draw(self):
        plt.rcParams['animation.html'] = 'jshtml'
        fig = plt.figure()
        ax = fig.add_subplot(111)
        self.set_size(6,1.8)
        fig.show()

        i = 0
        x, y = [], []

        while True:
            x.append(i)
            y.append(int(self.value))
            ax.set_xscale('linear')

            if self.mark_cycle:
                l1 = np.array((i, 0.5))
                ax.text(l1[0], l1[1], 'C'+str(self.cycle), fontsize=16,rotation=0, rotation_mode='anchor')
                self.mark_cycle=False
                
            ax.plot(x, y, color='black')
            if len(x) > 1:
                ax.axvspan(x[i-1], x[i], color=self.color)
            
            fig.canvas.draw()
            
            ax.set_xlim(left=max(0,i-20*self.period), right=i+5*self.period)
            ax.set_ylim(bottom=-0.2, top=1.2)

            time.sleep(0.1)
            i += 1

        plt.close()
        
    def set_size(self, w,h, ax=None):
        """ w, h: width, height in inches """
        if not ax: ax=plt.gca()
        l = ax.figure.subplotpars.left
        r = ax.figure.subplotpars.right
        t = ax.figure.subplotpars.top
        b = ax.figure.subplotpars.bottom
        figw = float(w)/(r-l)
        figh = float(h)/(t-b)
        ax.figure.set_size_inches(figw, figh)
    
    def __init__(self,id,period):
        self.id = id
        self.period = period
        self.value=True
        self.color = 'skyblue'
        self.mark_cycle=False
        self.cycle = 0
        self.system = System(1)
        self.thread = threading.Thread(target=self.thread_function)
        self.drw = threading.Thread(target=self.draw)

    def initialize_clock(self):
        #Se crea y ejecuta el hilo ejecuta el hilo
        self.thread.start()
        #self.drw.start()
        return
    

    
        
