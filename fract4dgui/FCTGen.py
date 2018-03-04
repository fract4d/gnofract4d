#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (C) 2006  Branko Kokanovic
#
#   FCTGen.py: generates .fct files
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA


import math
import os

from gi.repository import Gtk, GObject

from fract4d import fractal, fc, fractconfig

class FCTGeneration:
    def __init__(self,dir_bean,parent):
        self.dialog=Gtk.Dialog(
            "Generating .fct files...",parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL))
        
        self.pbar = Gtk.ProgressBar()
        self.dialog.vbox.pack_start(self.pbar,True,True,0)
        self.dialog.set_geometry_hints(None,min_aspect=3.5,max_aspect=3.5)
        self.dir_bean=dir_bean
        self.parent=parent
            
    def generate_fct(self):
        self.values=[]
        self.durations=[]
        version=self.find_version()
        if version=='-1':
            self.show_error("Could not find gnofract4d version. Can not continue")
            yield False
            return
        # -------------loads gnofract4d libs----------------------------
        try:
            self.fractal=fractal
            self.compiler=fc.Compiler()
            self.compiler.add_func_path("formulas")
            self.compiler.add_func_path("../formulas")
            self.compiler.add_func_path(
                fractconfig.T.get_data_path("formulas"))
        except:
            self.show_error("Gnofract4d libs could not be found")
            yield False
            return
        # --------------------------------------------------------------
        # find values from base keyframe first
        try:
            ret=self.find_values(self.dir_bean.get_base_keyframe())
            if len(ret)==11:
                self.values.append(ret)
            else:
                self.show_error("Unknown error during reading base keyframe")
                yield False
                return
        except:
            self.show_error("Unknown error during reading base keyframe")
            yield False
            return
        try:
            # find values and duration from all keyframes
            for i in range(self.dir_bean.keyframes_count()):
                ret=self.find_values(self.dir_bean.get_keyframe_filename(i))
                if len(ret)==11:
                    self.values.append(ret)
                elif len(ret)>1:
                    self.show_error("Error finding %s values in file: %s" % (ret[0],ret[1]))
                    yield False
                    return
                else:
                    self.show_error("Error reading .fct file")
                    yield False
                    return
                self.durations.append(self.dir_bean.get_keyframe_duration(i))
            # interpolate and write .fct files
            for i in range(self.dir_bean.keyframes_count()):
                if self.running is False:
                    yield False
                    break
                self.write_fct_file(i)
                percent=float(i+1)/float(self.dir_bean.keyframes_count())
                if self.running is False:
                    break
                self.pbar.set_fraction(percent)
                self.pbar.set_text(str(percent*100)+"%")
                yield True
        except:
            self.show_error("Unknown error during generation of .fct files")
            yield False
            return
            
        if self.running is False:
            yield False
            return
        self.running = False
        self.dialog.destroy()
        yield False

    def find_version(self):
        version='-1'
        pipe=os.popen("gnofract4d -v")
        line=pipe.readline()
        if line=='':
            return '-1'
        while line!='' and version=='-1':
            if line.startswith("Gnofract 4D"):
                version=line[12:len(line)].strip()
            line=pipe.readline()
        pipe.close()
        return version
            
    # finding x,y,z,w,size values from argument file and returns them as tuple
    def find_values(self,file):
        f=self.fractal.T(self.compiler)
        f.loadFctFile(open(file))
        x=f.params[f.XCENTER]
        y=f.params[f.YCENTER]
        z=f.params[f.ZCENTER]
        w=f.params[f.WCENTER]
        size=f.params[f.MAGNITUDE]
        xy=f.params[f.XYANGLE]
        xz=f.params[f.XZANGLE]
        xw=f.params[f.XWANGLE]
        yz=f.params[f.YZANGLE]
        yw=f.params[f.YWANGLE]
        zw=f.params[f.ZWANGLE]
        return (x,y,z,w,size,xy,xz,xw,yz,yw,zw)
    
    # interpolate values and writes .fct files
    def write_fct_file(self,iteration):
        # sum of all frames, needed for padding output files
        sumN=sum(self.durations)
        lenN=len(str(sumN))
        sumBefore=sum(self.durations[0:iteration])
        # current duration
        N=self.durations[iteration]
        # get content of file
        f=self.fractal.T(self.compiler)
        f.loadFctFile(open(self.dir_bean.get_base_keyframe()))
        # get all values
        x1=float(self.values[iteration][f.XCENTER])
        x2=float(self.values[iteration+1][f.XCENTER])
        y1=float(self.values[iteration][f.YCENTER])
        y2=float(self.values[iteration+1][f.YCENTER])
        z1=float(self.values[iteration][f.ZCENTER])
        z2=float(self.values[iteration+1][f.ZCENTER])
        w1=float(self.values[iteration][f.WCENTER])
        w2=float(self.values[iteration+1][f.WCENTER])
        size1=float(self.values[iteration][f.MAGNITUDE])
        size2=float(self.values[iteration+1][f.MAGNITUDE])
        xy1=float(self.values[iteration][f.XYANGLE])
        xy2=float(self.values[iteration+1][f.XYANGLE])
        xz1=float(self.values[iteration][f.XZANGLE])
        xz2=float(self.values[iteration+1][f.XZANGLE])
        xw1=float(self.values[iteration][f.XWANGLE])
        xw2=float(self.values[iteration+1][f.XWANGLE])
        yz1=float(self.values[iteration][f.YZANGLE])
        yz2=float(self.values[iteration+1][f.YZANGLE])
        yw1=float(self.values[iteration][f.YWANGLE])
        yw2=float(self.values[iteration+1][f.YWANGLE])
        zw1=float(self.values[iteration][f.ZWANGLE])
        zw2=float(self.values[iteration+1][f.ZWANGLE])
        # ------------find direction for angles----------------------
        to_right=[False]*6
        # ----------xy--------------
        dir_xy=self.dir_bean.get_directions(iteration)[0]
        if dir_xy==0:
            if abs(xy2-xy1)<math.pi and xy1<xy2:
                to_right[0]=True
            if abs(xy2-xy1)>math.pi and xy1>xy2:
                to_right[0]=True
        elif dir_xy==1:
            if abs(xy2-xy1)<math.pi and xy1>xy2:
                to_right[0]=True
            if abs(xy2-xy1)>math.pi and xy1<xy2:
                to_right[0]=True
        elif dir_xy==2:
            to_right[0]=True
        if to_right[0] is True and xy2<xy1:
                xy2=xy2+2*math.pi
        if to_right[0] is False and xy2>xy1:
                xy1=xy1+2*math.pi
        # --------------------------
        # ----------xz--------------
        dir_xz=self.dir_bean.get_directions(iteration)[1]
        if dir_xz==0:
            if abs(xz2-xz1)<math.pi and xz1<xz2:
                to_right[1]=True
            if abs(xz2-xz1)>math.pi and xz1>xz2:
                to_right[1]=True
        elif dir_xz==1:
            if abs(xz2-xz1)<math.pi and xz1>xz2:
                to_right[1]=True
            if abs(xz2-xz1)>math.pi and xz1<xz2:
                to_right[1]=True
        elif dir_xz==2:
            to_right[1]=True
        if to_right[1] is True and xz2<xz1:
                xz2=xz2+2*math.pi
        if to_right[1] is False and xz2>xz1:
                xz1=xz1+2*math.pi
        # --------------------------
        # ----------xw--------------
        dir_xw=self.dir_bean.get_directions(iteration)[2]
        if dir_xw==0:
            if abs(xw2-xw1)<math.pi and xw1<xw2:
                to_right[2]=True
            if abs(xw2-xw1)>math.pi and xw1>xw2:
                to_right[2]=True
        elif dir_xw==1:
            if abs(xw2-xw1)<math.pi and xw1>xw2:
                to_right[2]=True
            if abs(xw2-xw1)>math.pi and xw1<xw2:
                to_right[2]=True
        elif dir_xw==2:
            to_right[2]=True
        if to_right[2] is True and xw2<xw1:
                xw2=xw2+2*math.pi
        if to_right[2] is False and xw2>xw1:
                xw1=xw1+2*math.pi
        # --------------------------
        # ----------yz--------------
        dir_yz=self.dir_bean.get_directions(iteration)[3]
        if dir_yz==0:
            if abs(yz2-yz1)<math.pi and yz1<yz2:
                to_right[3]=True
            if abs(yz2-yz1)>math.pi and yz1>yz2:
                to_right[3]=True
        elif dir_yz==1:
            if abs(yz2-yz1)<math.pi and yz1>yz2:
                to_right[3]=True
            if abs(yz2-yz1)>math.pi and yz1<yz2:
                to_right[3]=True
        elif dir_yz==2:
            to_right[3]=True
        if to_right[3] is True and yz2<yz1:
                yz2=yz2+2*math.pi
        if to_right[3] is False and yz2>yz1:
                yz1=yz1+2*math.pi
        # --------------------------
        # ----------yw--------------
        dir_yw=self.dir_bean.get_directions(iteration)[4]
        if dir_yw==0:
            if abs(yw2-yw1)<math.pi and yw1<yw2:
                to_right[4]=True
            if abs(yw2-yw1)>math.pi and yw1>yw2:
                to_right[4]=True
        elif dir_yw==1:
            if abs(yw2-yw1)<math.pi and yw1>yw2:
                to_right[4]=True
            if abs(yw2-yw1)>math.pi and yw1<yw2:
                to_right[4]=True
        elif dir_yw==2:
            to_right[4]=True
        if to_right[4] is True and yw2<yw1:
                yw2=yw2+2*math.pi
        if to_right[4] is False and yw2>yw1:
                yw1=yw1+2*math.pi
        # --------------------------
        # ----------zw--------------
        dir_zw=self.dir_bean.get_directions(iteration)[5]
        if dir_zw==0:
            if abs(zw2-zw1)<math.pi and zw1<zw2:
                to_right[5]=True
            if abs(zw2-zw1)>math.pi and zw1>zw2:
                to_right[5]=True
        elif dir_zw==1:
            if abs(zw2-zw1)<math.pi and zw1>zw2:
                to_right[5]=True
            if abs(zw2-zw1)>math.pi and zw1<zw2:
                to_right[5]=True
        elif dir_zw==2:
            to_right[5]=True
        if to_right[5] is True and zw2<zw1:
                zw2=zw2+2*math.pi
        if to_right[5] is False and zw2>zw1:
                zw1=zw1+2*math.pi
        # --------------------------
        # ------------------------------------------------------------
        for i in range(N+1):
            # depending on interpolation type, mu constant get different values from 0 to 1
            int_type=self.dir_bean.get_keyframe_int(iteration)
            mu=float(i)/float(N)
            if int_type==INT_LINEAR:
                mu=mu
            elif int_type==INT_LOG:
                mu=math.log(mu+1,2)
            elif int_type==INT_INVLOG:
                mu=(math.exp(mu)-1)/(math.e-1)
            else:
                mu=(1-math.cos(mu*math.pi))/2
            # calculating new values
            new_x=x1*(1-mu)+x2*mu
            new_y=y1*(1-mu)+y2*mu
            new_z=z1*(1-mu)+z2*mu
            new_w=w1*(1-mu)+w2*mu
            new_size=size1*(1-mu)+size2*mu
            new_xy=xy1*(1-mu)+xy2*mu
            while new_xy>math.pi:
                new_xy=new_xy-2*math.pi
            new_xz=xz1*(1-mu)+xz2*mu
            while new_xz>math.pi:
                new_xz=new_xz-2*math.pi
            new_xw=xw1*(1-mu)+xw2*mu
            while new_xw>math.pi:
                new_xw=new_xw-2*math.pi
            new_yz=yz1*(1-mu)+yz2*mu
            while new_yz>math.pi:
                new_yz=new_yz-2*math.pi
            new_yw=yw1*(1-mu)+yw2*mu
            while new_yw>math.pi:
                new_yw=new_yw-2*math.pi
            new_zw=zw1*(1-mu)+zw2*mu
            while new_zw>math.pi:
                new_zw=new_zw-2*math.pi
            # replacing them in fractal
            f.params[f.XCENTER]=new_x
            f.params[f.YCENTER]=new_y
            f.params[f.ZCENTER]=new_z
            f.params[f.WCENTER]=new_w
            f.params[f.MAGNITUDE]=new_size
            f.params[f.XYANGLE]=new_xy
            f.params[f.XZANGLE]=new_xz
            f.params[f.XWANGLE]=new_xw
            f.params[f.YZANGLE]=new_yz
            f.params[f.YWANGLE]=new_yw
            f.params[f.ZWANGLE]=new_zw
            # writes .fct file
            folder=self.dir_bean.get_fct_dir()
            if folder[-1]!="/":
                folder=folder+"/"
            output=open(folder+"file_"+str(sumBefore+i).zfill(lenN)+".fct","w")
            f.save(output)

    def show_error(self,s):
        self.running=False
        self.error=True
        Gdk.threads_enter()
        error_dlg = Gtk.MessageDialog(
            self.dialog,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,s)
        error_dlg.run()
        error_dlg.destroy()
        Gdk.threads_leave()
        event = Gdk.Event(Gdk.EventType.DELETE)
        self.dialog.emit('delete_event', event)
    
    def show(self):
        self.dialog.show_all()
        self.running=True
        self.error=False
        task=self.generate_fct()
        GObject.idle_add(task.__next__)
        response = self.dialog.run()
        if response != Gtk.ResponseType.CANCEL:
            if self.running is True:  # destroy by user
                self.running=False
                self.dialog.destroy()
                return 1
            else:
                if self.error is True:  # error
                    self.dialog.destroy()
                    return -1
                else:  # everything ok
                    self.dialog.destroy()
                    return 0
        else:  # cancel pressed
            self.running=False
            self.dialog.destroy()
            return 1
