#!/usr/bin/env python
# coding: utf-8

# In[9]:


from time import time
from threading import Thread

import tkinter as tk
import tkinter.font as tkfont
from tkinter import Tk, Button, Label, PanedWindow, PhotoImage, Toplevel
from tkinter.simpledialog import askinteger
from tkinter.filedialog import askopenfilename

from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image, ImageTk

WIDTH = 194
RES = 200

class Classifier:
    
    def __init__(self, screen):
        self.res = RES
        self.model = None
        self.modelname = None
        self._modelname = None
        self.label = None
        self.labelname = None
        self._labelname = None
        
        self.screen = screen
        
        # display
        self.lbl_disp = Label(screen, text='nothing', height=8, fg='blue', bg='white')
        self.lbl_disp.pack(fill='x')
        self.lbl_cat = Label(screen, text='no label', fg='white', bg='brown')
        self.lbl_cat.pack(fill='x')

        # function buttons
        self.pnw_inp = PanedWindow(screen)
        self.pnw_inp.pack(fill='x')
        self.but_pic = Button(self.pnw_inp, text='classify...',
                              bg='green', fg='white', command=self.pic, state=tk.DISABLED)
        self.but_pic.pack(side='left', fill='x', expand=True)
        self.but_clear = Button(self.pnw_inp, text='clear', 
                                bg='yellow', command=self.clear)
        self.but_clear.pack(side='left', fill='x', expand=True)
        self.but_exit = Button(self.pnw_inp, text='exit', 
                               bg='red', command=window.destroy)
        self.but_exit.pack(side='left', fill='x', expand=True)
        
        # model buttons
        self.pnw_load = PanedWindow(screen)
        self.pnw_load.pack(fill='x')
        self.but_loadmodel = Button(self.pnw_load, text='model...', 
                                    bg='green', fg='white', command=self.loadmodel)
        self.but_loadmodel.pack(side='left', fill='x', expand=True)
        self.but_loadlabel = Button(self.pnw_load, text='labels...', 
                                    bg='green', fg='white', command=self.loadlabel)
        self.but_loadlabel.pack(side='left', fill='x', expand=True)
        self.but_res = Button(self.pnw_load, text='res...', 
                              bg='green', fg='white', command=self.setres)
        self.but_res.pack(side='left', fill='x', expand=True)
        
        # status
        self.lbl_status = Label(screen, text='')
        self.lbl_status.pack(fill='x')
    
    def clear(self):
        self.lbl_disp['text'] = 'nothing'
        self.lbl_disp.config(image='', height=8)
        self.lbl_cat['text'] = 'no label'
        self.lbl_status['text'] = ''
    
    def loadlabel(self):
        dlg = Toplevel()  # TopLevel would be triggered as a new dialog or screen
        dlg.title('labels...')
        dlg.resizable(width=False, height=False)
        
        AskLabels(dlg, self)
    
    def loadmodel(self):
        dlg = Toplevel()
        dlg.title('model...')
        dlg.resizable(width=False, height=False)
        
        AskModel(dlg, self)
            
    def pic(self):
        n = askopenfilename()
        if n:
            img = Image.open(n)

            # crop image
            w, h = img.size
            if h >= w:
                d = int((h - w) / 2)
                img = img.crop((0, d, w, h-d))
            else:  # h < w
                d = int((w - h) / 2)
                img = img.crop((d, 0, w-d, h))

            imgclsf = img.resize((self.res,)*2)
            imgshow = img.resize((WIDTH,)*2)
            imgtk = ImageTk.PhotoImage(image=imgshow)
            self.lbl_disp.imgtk = imgtk
            self.lbl_disp.config(image=imgtk, height=WIDTH)
            self.lbl_status['text'] = 'classifying...'
            self.but_pic['state'] = tk.DISABLED
            
            def classify(img):
                if not self.model:
                    return None

                #  pre-processing
                start = time()
                data = np.array(img.getdata())
                img = data.reshape(1, *img.size, 3)
                img = img.astype('float32')
                img /= 255.

                # predict
                p = np.argmax(self.model.predict(img))
                s = self.label[p] if self.label and p < len(self.label) else str(p)
                self.lbl_cat['text'] = s
                self.but_pic['state'] = tk.NORMAL
                self.lbl_status['text'] = f'classified for {(time() - start)*1000:,.0f} ms'
            Thread(target=classify, args=(imgclsf,)).start()
    
    def setres(self):
        n = askinteger('resolution...', f'resolution from {self.res} to')
        if n:
            self.res = n
        
class AskLabels:
    
    def __init__(self, screen, parent):
        self.screen = screen
        self.parent = parent
        self._labelname = None
        w = 11
        
        self.pnw_bar1 = PanedWindow(screen)
        self.pnw_bar1.pack(anchor='w')
        self.but_pick = Button(self.pnw_bar1, text='pick labels',
                               bg='green', fg='white', width=w, command=self.picklabels)
        self.but_pick.pack(side='left')
        self.lbl_disp = Label(self.pnw_bar1, text=f'{parent.labelname}')
        self.lbl_disp.pack(side='left', expand=True)
        self.pnw_bar1.update()
        
        self.but_remv = Button(screen, text='remove', width=w,
                               bg='green', fg='white', command=self.removelabels,
                               state=tk.NORMAL if parent.label else tk.DISABLED)
        self.but_remv.pack(anchor='w', expand=True)
        
        self.pnw_bar2 = PanedWindow(screen)
        self.pnw_bar2.pack(anchor='w')
        self.but_done = Button(self.pnw_bar2, text='load', width=w,
                               bg='green', fg='white', command=self.loadlabels,
                               state=tk.NORMAL if self._labelname else tk.DISABLED)
        self.but_done.pack(side='left')
        self.but_cncl = Button(self.pnw_bar2, text='cancel', 
                               bg='red', fg='black', command=screen.destroy)
        self.but_cncl.pack(side='left')
    
    def picklabels(self):
        self._labelname = None
        
        f = askopenfilename()
        if f:
            self._labelname = f
            self.lbl_disp['text'] = f
            self.but_done['state'] = tk.NORMAL
        else:
            self.but_done['state'] = tk.DISABLED
        
        self.screen.lift()  # to pop up the screen
                    
    def loadlabels(self):
        parent = self.parent
        
        if self._labelname:
            with open(self._labelname, encoding='utf-8') as f:
                parent.label = [n.strip() for n in f.readlines()]
            parent.labelname = self._labelname
            self._labelname = None
            parent.lbl_status['text'] = 'labels loaded done'
        else:
            parent.lbl_status['text'] = 'labels loading failed'
        
        self.screen.destroy()
            
    def removelabels(self):
        parent = self.parent
        
        if parent.label:
            parent.labelname = None
            parent.label = None
            parent.lbl_status['text'] = 'labels removed'
        else:
            parent.lbl_status['text'] = 'labels removing failed'
        
        self.screen.destroy()

class AskModel:
    
    def __init__(self, screen, parent):
        self.screen = screen
        self.parent = parent
        self._modelname = None
        w = 11
        
        self.bar1 = PanedWindow(screen)
        self.bar1.pack(anchor='w')
        self.but_pick = Button(self.bar1, text='pick model',
                               bg='green', fg='white', width=w, command=self.pickmodel)
        self.but_pick.pack(side='left')
        self.lbl_disp = Label(self.bar1, text=f'{parent.modelname}')
        self.lbl_disp.pack(side='left', expand=True)
        self.bar1.update()
        
        self.bar2 = PanedWindow(screen)
        self.bar2.pack(anchor='w')
        self.but_done = Button(self.bar2, text='load', width=w,
                               bg='green', fg='white', command=self.loadmodel,
                               state=tk.NORMAL if self._modelname else tk.DISABLED)
        self.but_done.pack(side='left')
        self.but_cncl = Button(self.bar2, text='cancel',
                               bg='red', fg='black', command=screen.destroy)
        self.but_cncl.pack(side='left')
    
    def pickmodel(self):
        self._modelname = None
        
        f = askopenfilename()
        if f:
            self._modelname = f
            self.lbl_disp['text'] = f
            self.but_done['state'] = tk.NORMAL
        else:
            self.but_done['state'] = tk.DISABLED
        
        self.screen.lift()
                    
    def loadmodel(self):
        parent = self.parent
        
        if self._modelname:
            parent.but_pic['state'] = tk.DISABLED
            parent.lbl_status['text'] = 'loading model...'
            
            def load():
                start = time()
                parent.model = load_model(self._modelname)
                parent.modelname = self._modelname
                parent.lbl_status['text'] = f'model loaded for {time() - start:,.2f} secs'
                parent.but_pic['state'] = tk.NORMAL
                self._modelname = None
            Thread(target=load).start()
        else:
            parent.lbl_status['text'] = 'model loading failed'
        
        self.screen.destroy()
    
window = Tk()
tkfont.nametofont("TkDefaultFont").configure(size=14)
window.title('分類器')
window.geometry(f'{WIDTH+70}x350')
window.resizable(width=False, height=False)

Classifier(window)
window.mainloop()


# In[ ]:




