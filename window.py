#! /usr/bin/env python

import wx
import os
import subprocess
import thread
import localwoof

MAIN_WINDOW_DEFAULT_SIZE = (300,200)

# Creates a file drop target
class FileDropTarget(wx.FileDropTarget):
    def __init__(self, obj):
        wx.FileDropTarget.__init__(self)
        self.obj = obj
    
    # Defines what to do when files get dropped on the target
    def OnDropFiles(self, x, y, filenames):
        if len(filenames) > 1:
            popup = wx.MessageDialog(self.obj, "wxWoof only supports single files to host. Compress your directory and/or files into a zip or something, first!", "Too many files!", wx.OK | wx.ICON_INFORMATION)
            popup.ShowModal()
            return
        
        # This only runs with the first file
        for filename in filenames:
            filePath = filename.encode('ascii')
            self.obj.GetParent().filePath = filePath
            self.obj.GetParent().simpleName = os.path.split(filePath)[1]
            self.obj.GetParent().fileNameLabel.SetLabel("File selected: " + self.obj.GetParent().simpleName)
            bitmap = self.obj.GetParent().closeImage
            self.obj.GetParent().boxButton.bitmap = bitmap
            self.obj.GetParent().boxButton.SetBitmapLabel(bitmap)
            self.obj.GetParent().boxButton.Update()
    

# Creates a frame (our main window)
class Frame(wx.Frame):
    __slots__ = ['height', 'width'] 
    
    def __init__(self, parent, id, title):
        self.height = 200;
        self.width = 300;
        
        # locking flag
        self.lock = False
        
        # filePath string
        self.filePath = ""
        
        # Make the style of the frame non-resizable, set the other params
        style = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER)
        self.frame = wx.Frame.__init__(self, parent, id, title = title, size = MAIN_WINDOW_DEFAULT_SIZE, style = style)
        
        # puts the frame in the center of the screen
        self.Center()
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour('White')
        
        # Create my buttons and labels
        self.fileNameLabel = wx.StaticText(self, 1, 'No file selected', pos=(5, 5), size=(290,-1), style=wx.ALIGN_CENTER)
        self.hostingLocationLabel = wx.StaticText(self, 8, '', pos=(5, 150), size=(290,-1), style=wx.ALIGN_CENTER)
        
        self.dragTip = wx.StaticText(self, 2, 'Select by dragging onto, or clicking, the box.', pos=(5, 22), size=(290,-1), style=wx.ALIGN_CENTER)
        
        # Make a button that will take the dropped file.        
        # Grab the cool "open box" image, make it a bitmap
        imgNameOp = "box_open.jpg"
        imgNameCl = "box_close.jpg"
        self.openImage = wx.Image(imgNameOp, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.closeImage = wx.Image(imgNameCl, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        
        # Create a bitmap button, bind to select file function
        self.boxButton = wx.BitmapButton(self, 3, bitmap=self.openImage, pos=(120,45), size=(60,60))
        self.Bind(wx.EVT_BUTTON, self.OnOpen, id = 3)
        
        # Make the button the drop target by making a drop target, and linking
        self.dropTarget = FileDropTarget(self.boxButton)
        self.boxButton.SetDropTarget(self.dropTarget)
        
        # Create the button to start the hosting, bind to host function
        self.hostButton = wx.Button(self, 4, 'Click here to host!', (80, 110))
        self.Bind(wx.EVT_BUTTON, self.OnHost, id = 4)
    
    
    # Defines the file selection behavior
    def OnOpen(self, event):
        if self.lock:
            return
        
        dlg = wx.FileDialog(self, message = "Select a file...", defaultDir = os.getcwd(), defaultFile = "", style = wx.OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            if len(dlg.GetPaths()) > 1:
                popup = wx.MessageDialog(self, "wxWoof only supports single files to host. Compress your directory and/or files into a zip or something, first!", "Too many files!", wx.OK | wx.ICON_INFORMATION)
                popup.ShowModal()
                return
                
            self.filePath = dlg.GetPath()
            self.simpleName = os.path.split(self.filePath)[1]
            self.fileNameLabel.SetLabel("File selected: " + self.simpleName)
            self.boxButton.bitmap = self.closeImage
            self.boxButton.SetBitmapLabel(self.closeImage)
            self.boxButton.Update()
        dlg.Destroy()
    
    
    # Defines the exit behavior
    def OnExit(self, event):
        self.Destroy()
    
    
    # Defines the hosting behavior. Locks the UI and calls local woof.
    def OnHost(self, event):
        if "No file selected" == self.fileNameLabel.GetLabel():
            return
        elif "Hosting file..." == self.fileNameLabel.GetLabel():
            return
        elif self.lock == False:
            self.lock = True
            self.hostButton.Disable()
            self.boxButton.Disable()
            self.fileNameLabel.SetLabel("Hosting file...")
            myIp = localwoof.find_ip()
            self.hostingLocationLabel.SetLabel("D/L ip: " + myIp + ":8080")
            thread.start_new_thread(self.LaunchWoof, ())
        
        elif self.lock == True:
            self.fileNameLabel.SetLabel("Already hosting file!")
    
    
    # Launches the local woof if not locked.
    def LaunchWoof(self):
        print 'Running using path: ' + self.filePath
        success = localwoof.launch(self.filePath)
        if success:
            print "wxWoof: Sucess acknowledged"
            self.lock = False
            self.fileNameLabel.SetLabel("File selected: " + self.simpleName)
        else:
            print "wxWoof: Hosting failed"
            # fail cleanup


# Defines our main application
class App(wx.App):
    
    def OnInit(self):
        self.frame = Frame(parent = None, id = 100, title = 'Woof')
        self.frame.Show()
        self.frame.Refresh(True)
        self.SetTopWindow(self.frame)
        return True
    

if __name__ == "__main__":
    app = App(redirect = False)
    app.MainLoop()