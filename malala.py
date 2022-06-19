#!/usr/bin/env python
# coding: utf-8

# # MaLaLa stands for Multi-Label Labler

# In[1]:


import os
from base64 import b64decode
from io import BytesIO
from time import time
from functools import partial
from collections import OrderedDict
from copy import deepcopy
import tkinter as tk
import tkinter.font as tkfont
from tkinter import Tk, Button, Label, PanedWindow, PhotoImage, Frame
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from tkinter.messagebox import showinfo

from PIL import Image, ImageTk

from resource import *


# In[2]:


NAME = 'MaLaLa'
RES = 400
PUSHED_RFB = [[tk.RAISED, 'white', 'green'], [tk.SUNKEN, 'green', 'white']]
STATUS_FG = {'normal': 'black', 'alert': 'red'}


# In[3]:


class Trees:
    
    def __init__(self, root=None):
        self.base(root)
    
    def __len__(self):
        return len(self.pics)
    
    def base(self, path, append=False):
        '''Search image files of specific path
        path - .jpg files for searching from
        return - file names of .jpg list
        '''
        
        files = self._search_jpg(path) if path else []
        if append:
            count = 0
            for f in files:
                if f not in self.pics:
                    self.pics.append(f)
                    self.anns[f] = []
                    count += 1
            return count

        self.pics = files
        self.anns = OrderedDict(zip(self.pics, [[]]*len(self.pics)))
        return len(files)
    
    def add(self, name, labels=None):
        '''Add an file name and annotation mapping. If name is existed, annotation
        would be replaced or cleared.
        name - file name of image
        labels - in iterable, ex: [0, 2, 5]
        return - True for success
               - False for file name not existed
        '''
        
        if name not in self.pics:
            if os.path.isfile(name):
                self.pics.append(name)
            else:
                return False
        self.anns[name] = sorted(set(labels)) if labels else []
        return True
    
    def ann(self, name, labels):
        '''Annotate the image of a file.
        name - file name of image
        labels - in iterable, ex: [0, 2, 5]
        return - True for success
               - False for no such name
        '''
        
        if name not in self.anns:
            return False
        
        self.anns[name] = sorted(set(labels)) if labels else []
        return True
    
    def nna(self, name):
        '''Read the annotation of an image file.
        name - file name of image
        return - annotation in list, ex: [0, 2, 5]
               - None for invalid name
        '''
        
        if name not in self.anns:
            return None
        
        return deepcopy(self.anns[name])
    
    def nnai(self, i):
        '''Read the annotation of an image file.
        i - index of image
        return - annotation in list, ex: [0, 2, 5]
               - None for invalid name
        '''
        
        if i < 0 or i >= len(self.anns):
            return None
        
        return deepcopy(self.anns[self.pics[i]])
    
    def annout(self, filename, applytoall=None):
        '''Outout the annotations to the specific file.
        filename - output file
        applytoall - same annotatios for all images, overwrite previous and individual ones
        return - True for success
               - False for failure
        '''
        
        if not filename:
            return False
        
        with open(filename, 'w', encoding='utf-8') as f:
            if applytoall:
                a = ','.join([str(c) for c in applytoall])
                rows = [f'{e},{a}\n' for e in self.anns]
            else:
                rows = [f"{e},{','.join([str(c) for c in self.anns[e]])}\n" for e in self.anns]
            f.writelines(rows)
        return True
    
    def annin(self, filename, append=False):
        '''Load annotations from filename.
        filename - file of annotations
        append - flag for appending new annotations
        return - count of successfully loaded annotations
        '''
        with open(filename, encoding='utf-8') as f:
            newtree = not self.pics
            newfns = [self.ann, self.add]
            line = f.readline()
            count = 0
            while line:
                n, *a = line.strip().split(',')
                if n:
                    ann = [int(aa) for aa in a if aa] if a else []
                    count += int(newfns[int(newtree or append)](n, ann))
                line = f.readline()
            return count
    
    def _search_jpg(self, path):
        files = []
        for _p in os.listdir(path):
            p = os.path.join(path, _p)
            if os.path.isdir(p):
                files.extend(self._search_jpg(p))
            elif os.path.isfile(p) and p.endswith(('.jpg', '.JPG')):
                files.append(p)
        return files


# In[4]:


class Malala:
    
    def __init__(self, screen):
        self.label = None
        self.trees = None
        self.pici = -1
        self.labels = []
        self.screen = screen
        self.pnw_labels = None
        
        # screen        
        screen.title(NAME)
        screen.iconphoto(False, PhotoImage(data=b64decode(wt_icon_bg_png)))
        screen.geometry(f'{RES+270}x{RES+80}')
        screen.resizable(width=True, height=False)
        screen.bind('<Control-s>', self.save_annos)
        
        # status
        self.lbl_status = Label(screen, text='', bg='white')
        self.lbl_status.pack(fill='x', side='bottom')
        
        # display
        self.pnw_main = PanedWindow(screen, width=RES)
        self.pnw_main.pack(fill='both', side='left', expand=True)
        self.frm_disp = Frame(self.pnw_main, height=RES, width=RES, bg='white')
        self.frm_disp.pack(fill='both', expand=True, side='top')
        self.lbl_disp = Label(self.frm_disp, bg='white')
        self.lbl_disp.pack(fill='both', expand=True)
        self.lbl_disp.bind('<Button>', self.pop)
        # navigators
        self.pnw_nav = PanedWindow(self.pnw_main)
        self.pnw_nav.pack(fill='x', side='top', expand=False)
        self.but_start = Button(self.pnw_nav, text='|<', fg='white', bg='brown',
                                command=lambda: self.do_pic('|<'))
        self.but_start.pack(fill='x', side='left')
        self.but_prev = Button(self.pnw_nav, text='<', fg='white', bg='brown',
                               command=lambda: self.do_pic('<'))
        self.but_prev.pack(fill='x', side='left')
        self.but_end = Button(self.pnw_nav, text='>|', fg='white', bg='brown',
                              command=lambda: self.do_pic('>|'))
        self.but_end.pack(fill='x', side='right')
        self.but_next = Button(self.pnw_nav, text='>', fg='white', bg='brown',
                               command=lambda: self.do_pic('>'))
        self.but_next.pack(fill='x', side='right')
        self.lbl_file = Label(self.pnw_nav, text='no file', anchor='e', wraplength=RES-140)
        self.lbl_file.pack(side='right')
        
        # dock region
        self.pnw_dock = PanedWindow(screen)
        self.pnw_dock.pack(fill='both', side='right')
        
        # support functions
        self.pnw_supp = PanedWindow(self.pnw_dock)
        self.but_zoom = Button(self.pnw_supp, text='zoom', width=5, anchor='w', 
                                bg='magenta', fg='white', command=self.zoom)
        self.but_zoom.pack(side='left', fill='x', expand=False)
        self.pnw_supp.pack(fill='x', side='bottom', anchor='s')
        self.but_clear = Button(self.pnw_supp, text='clear', width=5, anchor='w',
                                bg='yellow', command=self.clear)
        self.but_clear.pack(side='left', fill='x', expand=False)
        self.but_about = Button(self.pnw_supp, text='about...', width=5, anchor='w', 
                                bg='blue', fg='white', command=self.about)
        self.but_about.pack(side='left', fill='x', expand=False)
        self.but_exit = Button(self.pnw_supp, text='exit', width=5, anchor='w',
                               bg='red', fg='white', command=window.destroy)
        self.but_exit.pack(side='left', fill='x', expand=False)
        
        # annotation functions
        self.pnw_anno = PanedWindow(self.pnw_dock)
        self.pnw_anno.pack(fill='x', side='bottom')
        lbl_annos = Label(self.pnw_anno, text='annos', width=5, anchor='w')
        lbl_annos.pack(side='left', padx=2)
        self.but_lannos = Button(self.pnw_anno, text='load...', width=5, anchor='w',
                                 bg='gray', fg='white', command=self.load_annos)
        self.but_lannos.pack(side='left', fill='x')
        self.but_aannos = Button(self.pnw_anno, text='more...', width=5, anchor='w',
                                 bg='gray', fg='white', command=lambda: self.load_annos(True))
        self.but_aannos.pack(side='left', fill='x')
        self.but_sannos = Button(self.pnw_anno, text='save...', width=5, anchor='w',
                                 bg='gray', fg='white', command=self.save_annos)
        self.but_sannos.pack(side='left', fill='x')
        
        # main functions
        self.pnw_func = PanedWindow(self.pnw_dock)
        self.pnw_func.pack(fill='x', side='bottom')
        lbl_pics = Label(self.pnw_func, text='pics', width=5, anchor='w')
        lbl_pics.pack(side='left', padx=2)
        self.but_dir = Button(self.pnw_func, text='base...', width=5, anchor='w',
                              bg='gray', fg='white', command=self.pic_base)
        self.but_dir.pack(side='left', fill='x')
        self.but_mdir = Button(self.pnw_func, text='more...', width=5, anchor='w',
                              bg='gray', fg='white', command=lambda: self.pic_base(True))
        self.but_mdir.pack(side='left', fill='x')
        self.but_labels = Button(self.pnw_func, text='labels...', width=5, anchor='w',
                                 bg='gray', fg='white', command=self.load_labels)
        self.but_labels.pack(side='left', fill='x')
    
    def status(self, desc, mode='normal'):
        self.lbl_status.config(fg=STATUS_FG[mode], text=(desc or 'None'))
    
    def zoom(self):
        global RES
        if self.but_zoom['relief'] == tk.RAISED:
            RES, relief, fg, bg = 600, tk.SUNKEN, 'magenta', 'white'
        else:
            RES, relief, fg, bg = 400, tk.RAISED, 'white', 'magenta'
        
        # redraw
        self.screen.geometry(f'{RES+270}x{RES+80}')
        self.but_zoom.config(relief=relief, fg=fg, bg=bg)
        self.lbl_file.config(wraplength=RES-140)
        if self.pici >= 0:
            self.pic(self.trees.pics[self.pici])
    
    def pop(self, event):
        if self.pici >= 0:
            os.system(self.trees.pics[self.pici])
    
    def about(self):
        showinfo(f'about {NAME}', f'{NAME}, a Multi-label Labeler\n\n' +
                 'Copyright © 2022 Enos Chou')
    
    def do_pic(self, direction):
        if not self.trees or not len(self.trees):
            return
        
        pici = self.nav(direction)
        if pici == None or pici == self.pici:
            return
        
        labeltoall = (self.labels and self.but_applytoall['relief'] == tk.SUNKEN)
        if self.pici >= 0 and self.labels and not labeltoall:
            self.anno(self.trees.pics[self.pici])  # save last pic annotation
        
        self.pici = pici
        p = self.trees.pics[pici]
        self.pic(p)  # draw new pic
            
        if not self.labels:
            self.draw_labels()  # clear labels
        elif not labeltoall:
            self.switch_labus(self.trees.nna(p))  # switch label button with min refresh
            
    def nav(self, direction):
        if direction == '|<':
            i = 0
        elif direction == '<':
            i = 0 if not self.pici else self.pici - 1
        else:
            end = len(self.trees) - 1
            i = end if direction == '>|' or self.pici == end else self.pici + 1
        return i
    
    def crop(self, img):
        w, h = img.size
        if h >= w:
            d = int((h - w) / 2)
            return img.crop((0, d, w, h-d))
        d = int((w - h) / 2)
        return img.crop((d, 0, w-d, h))
    
    def rotate(self, img):
        exif = img._getexif()
        orientation = -2
        if exif:
            orientation = exif.get(274, -1)
        if orientation > 1:
            #print(orientation)
            if orientation == 6:  # enos have to fine tune for more orientation later
                img = img.rotate(270)
        return img
    
    def pic(self, picn):
        img = Image.open(picn)
        img = self.rotate(img)  # rotate to the correct direction
        img = self.crop(img)
        
        # draw
        img = img.resize((RES,)*2)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lbl_disp.imgtk = imgtk
        self.lbl_disp.config(image=imgtk)
        
        # note pic name
        self.lbl_file['text'] = picn
    
    def anno(self, picn):
        buts = self.but_labels
        a = [i for i, but in enumerate(buts) if but['relief'] == tk.SUNKEN]
        self.trees.ann(picn, a)
    
    def reset_applytoall(self):
        if self.labels and self.but_applytoall['relief'] == tk.SUNKEN:
            self.on_applytoall()
    
    def pic_base(self, more=False):
        d = askdirectory(title='Select directory of images')
        if d:
            self.reset_applytoall()
            if more and self.trees:
                count = self.trees.base(d, True)
                self.status(f'{d} selected more {count:,} pics')
            else:
                self.trees = Trees(d)
                self.status(f'{d} selected {len(self.trees):,} pics')
                self.pici = -1
                self.do_pic('|<')
    
    def clear(self):
        self.lbl_disp.config(image='')
        self.lbl_status['text'] = ''
        self.lbl_file['text'] = 'no file'
        self.trees = None
        self.pici = -1
        self.label = None
        self.labels = []
        if self.pnw_labels:
            self.pnw_labels.destroy()
            self.pnw_labels = None
    
    def load_labels(self):
        d = askopenfilename(title='Select labels file')
        if d:
            try:
                with open(d, encoding='utf-8') as f:
                    self.labels = [line.strip() for line in f.readlines()]
                self.status(f'{d} {len(self.labels)} labels loaded')
                self.draw_labels(self.trees.nnai(self.pici) if self.trees else None)
            except Exception as e:
                self.status(e, mode='alert')
            
    def on_press(self, keyi):
        pushed = self.but_labels[keyi]['relief'] == tk.RAISED        
        relief, fg, bg = PUSHED_RFB[int(pushed)]
        self.but_labels[keyi].config(relief=relief, fg=fg, bg=bg)
    
    def on_applytoall(self):
        cmap = {tk.RAISED: {'relief': tk.SUNKEN, 'fg': 'brown', 'bg': 'white'},
                tk.SUNKEN: {'relief': tk.RAISED, 'fg': 'white', 'bg': 'brown'}}
        self.but_applytoall.config(**cmap[self.but_applytoall['relief']])
    
    def load_annos(self, append=False):
        d = askopenfilename(title='Select annotation file')
        if d:
            newtrees = not self.trees
            if newtrees:
                self.trees = Trees()
                self.pici = -1
            try:
                count = self.trees.annin(d, append)
            except Exception as e:
                if newtrees:
                    self.trees = None
                self.status(e, 'alert')
                return
            
            if count > 0:
                if newtrees:
                    self.do_pic('|<')
                elif self.labels:
                    self.reset_applytoall()
                    self.switch_labus(self.trees.nnai(self.pici))
            
            if count == 0:
                self.status(f'{d} no annotation loaded', 'alert')
            else:
                self.status(f'{d} {count:,} annotations loaded')
    
    def save_annos(self, event=None):
        if self.trees:
            if event and self.label:  # ctrl-s
                d = self.label
            else:
                d = asksaveasfilename(title='Select or new annotation file')
            if d:
                if self.labels and self.but_applytoall['relief'] == tk.SUNKEN:
                    a = [i for i, b in enumerate(self.but_labels) if b['relief'] == tk.SUNKEN]
                    r = self.trees.annout(d, a)  # save with applytoall
                else:    
                    if self.pici >= 0 and self.labels:
                        self.anno(self.trees.pics[self.pici])  # annotate last image
                    r = self.trees.annout(d)  # output annotations to file
                if r:
                    self.label = d
                    self.status(f'output annotations to {d} done')
                else:
                    self.status(f'output annotations to {d} failed!', 'alert')
    
    def switch_labus(self, anno):
        # [0, 5, 9] ==> [2, 9]
        # 0: RAISED, 1: nothing, 5: RAISED, 2: SUNKEN, 9: nothing
        for i in range(len(self.but_labels)):
            if self.but_labels[i]['relief']==tk.SUNKEN:
                if i not in anno:
                    relief, fg, bg = PUSHED_RFB[0]
                    self.but_labels[i].config(relief=relief, fg=fg, bg=bg)
            elif i in anno:
                relief, fg, bg = PUSHED_RFB[1]
                self.but_labels[i].config(relief=relief, fg=fg, bg=bg)
    
    def draw_labels(self, anno=None):
        if self.pnw_labels:
            self.pnw_labels.destroy()
        self.pnw_labels = PanedWindow(self.pnw_dock)
        self.pnw_labels.pack(fill='x', side='top', expand=False)
        
        if self.labels:
            self.but_applytoall = Button(self.pnw_labels, text='Apply to All', fg='white',
                                         bg='brown', command=self.on_applytoall)
            self.but_applytoall.pack(fill='x', side='top')
            w = 3
            lay = int(len(self.labels) / w) + int(bool(len(self.labels) % w))
            self.but_labels = []
            i = 0
            for la in range(lay):
                pnw_lay = PanedWindow(self.pnw_labels)
                pnw_lay.pack(fill='x', side='top', expand=False)
                a = 0
                while i < len(self.labels) and a < w:
                    pushed = bool(anno and i in anno)
                    relief, fg, bg = PUSHED_RFB[int(pushed)]
                    b = Button(pnw_lay, text=self.labels[i], bg=bg, fg=fg, width=7, anchor='w',
                               command=partial(self.on_press, i), relief=relief)
                    b.pack(side='left', fill='x', expand=False)
                    self.but_labels.append(b)
                    i += 1
                    a += 1


# In[5]:


window = Tk()
tkfont.nametofont("TkDefaultFont").configure(size=14)
Malala(window)
window.mainloop()


# In[ ]:




