#! /usr/bin/env python

import wx
import os
import subprocess

MAIN_WINDOW_DEFAULT_SIZE = (300,100)

class Frame(wx.Frame):
	
	def __init__(self, parent, id, title):
		# locking flag
		self.lock = False
		
		# filePath string
		self.filePath = ""
		
		# not sure what this does...
		style = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER)
		self.frame = wx.Frame.__init__(self, parent, id, title = title, size = MAIN_WINDOW_DEFAULT_SIZE, style = style)
		
		# puts the frame in the center of the screen
		self.Center()
		self.panel = wx.Panel(self)
		self.panel.SetBackgroundColour('White')
		
		# Create my button, label, and menu bar
		self.selectButton = wx.Button(self, 2, 'Select File', (50, 40))
		self.hostButton = wx.Button(self, 3, 'Begin Hosting', (150, 40))
		self.fileNameLabel = wx.StaticText(self, 4, 'No file selected', (100, 15))
		
		# Binds, on click, the LaunchWoof function to my button, which has id 3
		self.Bind(wx.EVT_BUTTON, self.LaunchWoof, id = 3)
		self.Bind(wx.EVT_BUTTON, self.OnOpen, id = 2)
	
	
	def OnOpen(self, event):
		if self.lock:
			return
		
		dlg = wx.FileDialog(self, message = "Select a file...", defaultDir = os.getcwd(), defaultFile = "", style = wx.OPEN)
		
		if dlg.ShowModal() == wx.ID_OK:
			self.filePath = dlg.GetPath()
			self.simpleName = os.path.split(self.filePath)[1]
			self.fileNameLabel.SetLabel("File selected: " + self.simpleName)
			
		dlg.Destroy()
	
	
	def OnExit(self, event):
		self.Destroy()
	
	
	def LaunchWoof(self, event):
		if "No file selected" == self.fileNameLabel.GetLabel():
			return
			
		elif "Hosting file..." == self.fileNameLabel.GetLabel():
			return
			
		elif self.lock == False:
			child_pid = os.fork()
			if child_pid == 0:
				# child 
				os.execvp('python', ['', 'woof', self.filePath])
			else:
				# parent
				self.lock = True
				self.fileNameLabel.SetLabel("Hosting file...")					
	




class App(wx.App):
	
	def OnInit(self):
		self.frame = Frame(parent = None, id = 5, title = 'Woof')
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True
	


if __name__ == "__main__":
	app = App(redirect = False)
	app.MainLoop()