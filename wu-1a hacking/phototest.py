#!/usr/bin/env python

import Tkinter 
from PIL import Image, ImageTk
import StringIO
import pyptpip
import struct

class LiveViewer:
	def __init__(self,frame):

		self.s1=pyptpip.connectptpip()
		data=pyptpip.initcmdreq(self.s1)
		self.sessionid=data[:4]

		self.s2=pyptpip.connectptpip()
		data=pyptpip.initeventreq(self.s2,self.sessionid)

		pyptpip.cmdreqnodata(self.s1,0x1002,self.sessionid)
		pyptpip.cmdreqnodata(self.s1,0x9201)

		# create and place a canvas with the image in it
		imagefile="eee.jpg"
		image1 = ImageTk.PhotoImage(Image.open(imagefile))
		self.canvas=Tkinter.Canvas(frame,width=640,height=480)
		self.canvas.create_image(0,0,anchor='nw',image=image1)
		self.canvas.image=image1
		self.canvas.grid(row=0,columnspan=10)

		# create and place buttons. need to add handlers.
		buttonUp = Tkinter.Button(frame, text='^',command=self.Up) # 0x9205, x, y
		buttonDown = Tkinter.Button(frame, text='V',command=self.Down)
		buttonLeft = Tkinter.Button(frame, text='<',command=self.Left)
		buttonRight = Tkinter.Button(frame, text='>',command=self.Right)

		buttonOutOut = Tkinter.Button(frame, text='--',command=self.OutOut)  #0x1015, 0xD1A3, 0x00
		buttonOut = Tkinter.Button(frame, text='-',command=self.Out)  #0x1015, 0xD1A3, -1 
		buttonShoot = Tkinter.Button(frame, text='X',command=self.Shoot) #0x9207, 0xFFFFFFFF, 0x000 
		buttonIn = Tkinter.Button(frame, text='+',command=self.In) #0x1015, 0xD1A3, +1
		buttonInIn = Tkinter.Button(frame, text='++',command=self.InIn) #0x1015, 0xD1A3, 0x05

		buttonFocusInIn = Tkinter.Button(frame, text='<<',command=self.FocusInIn)  #0x9204, 0x02, 0x10
		buttonFocusIn = Tkinter.Button(frame, text='<',command=self.FocusIn)  #0x9204, 0x02, 0x01
		buttonAF = Tkinter.Button(frame, text='AF',command=self.AF)  #0x90C1
		buttonFocusOut = Tkinter.Button(frame, text='>',command=self.FocusOut) #0x9204, 0x01, 0x01
		buttonFocusOutOut = Tkinter.Button(frame, text='>>',command=self.FocusOutOut) #0x9204, 0x01, 0x10

		buttonUp.grid(row=1,column=1)
		buttonDown.grid(row=3,column=1)
		buttonLeft.grid(row=2,column=0)
		buttonRight.grid(row=2,column=2)

		buttonOutOut.grid(row=1,column=4)
		buttonOut.grid(row=1,column=5)
		buttonShoot.grid(row=1,column=6)
		buttonIn.grid(row=1,column=7)
		buttonInIn.grid(row=1,column=8)

		buttonFocusInIn.grid(row=2,column=4)
		buttonFocusIn.grid(row=2,column=5)
		buttonAF.grid(row=2,column=6)
		buttonFocusOut.grid(row=2,column=7)
		buttonFocusOutOut.grid(row=2,column=8)

		self.zoomlevel=0x00

		self.frame=frame
		self.poll()


	def __del__(self):
		self.s1.close()
		self.s2.close()

	def poll(self):
		while (pyptpip.cmdreqnodata(self.s1,0x90c8)!=0x2001):
			pass
		(data,code,response)=pyptpip.cmdreqgetdata(self.s1,0x9203)
		imagefile=StringIO.StringIO(data[0x180:])
		image1=ImageTk.PhotoImage(Image.open(imagefile))
		self.canvas=Tkinter.Canvas(self.frame,width=640,height=480)
		self.canvas.create_image(0,0,anchor='nw',image=image1)
		self.canvas.image=image1
		self.canvas.grid(row=0,columnspan=10)
		self.frame.after(5,self.poll)
		
	def Up(self): # 0x9205, x, y
		pass

	def Down(self):
		pass

	def Left(self):
		pass
	
	def Right(self):
		pass

	def OutOut(self):  #0x1015, 0xD1A3, 0x00
		print "outout"
		self.zoomlevel=0x00
		pyptpip.cmdreqsenddata(self.s1,0x1016,struct.pack("I",0xD1A3),struct.pack("B",self.zoomlevel))
		print "done"

	def Out(self):  #0x1015, 0xD1A3, -1 
		print "out"
		if (self.zoomlevel>0):
			self.zoomlevel-=1
		pyptpip.cmdreqsenddata(self.s1,0x1016,struct.pack("I",0xD1A3),struct.pack("B",self.zoomlevel))
		print "done"

	def Shoot(self): #0x9207, 0xFFFFFFFF, 0x000 
		print "shoot"
		print hex(pyptpip.cmdreqnodata(self.s1,0x9207,struct.pack("II",0xFFFFFFFF,0x00)))

	def In(self): #0x1015, 0xD1A3, +1
		print "in"
		if (self.zoomlevel<5):
			self.zoomlevel+=1
		pyptpip.cmdreqsenddata(self.s1,0x1016,struct.pack("I",0xD1A3),struct.pack("B",self.zoomlevel))
		print "done"

	def InIn(self): #0x1015, 0xD1A3, 0x05
		print "inin"
		self.zoomlevel=0x05
		pyptpip.cmdreqsenddata(self.s1,0x1016,struct.pack("I",0xD1A3),struct.pack("B",self.zoomlevel))
		print "done"

	def FocusInIn(self):  #0x9204, 0x02, 0x10
		print hex(pyptpip.cmdreqnodata(self.s1,0x9204,struct.pack("II",0x02,0x0100)))

	def FocusIn(self):  #0x9204, 0x02, 0x01
		print hex(pyptpip.cmdreqnodata(self.s1,0x9204,struct.pack("II",0x02,0x010)))

	def AF(self):  #0x90C1
		pyptpip.cmdreqnodata(self.s1,0x90c1)

	def FocusOut(self): #0x9204, 0x01, 0x01
		print hex(pyptpip.cmdreqnodata(self.s1,0x9204,struct.pack("II",0x01,0x010)))

	def FocusOutOut(self): #0x9204, 0x01, 0x10
		print hex(pyptpip.cmdreqnodata(self.s1,0x9204,struct.pack("II",0x01,0x0100)))

root = Tkinter.Tk()
app=LiveViewer(root)
# press go
root.mainloop()


