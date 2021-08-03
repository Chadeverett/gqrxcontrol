'''
Created on 9/28/2019

@author: chad brown
'''
import os
import telnetlib
import socket
import threading
import time
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.slider import Slider
from kivy.app import App
from kivy.config import Config
from kivy.clock import Clock, mainthread
from kivy.storage.dictstore import DictStore
from kivy.uix.settings import SettingsWithSidebar
from json_settings import json_settings
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
Window.size = (400, 450)

DEBUGLVL = 3

Builder.load_string('''
<Interface>:
    orientation: 'vertical'
    Button:
        size_hint_y: None
        height: 35
        text: 'Settings'
        on_release: app.open_settings()
    Widget:
''')


bookmarks = [
    {'frequency':'147090000', 'mode':'FM', 'filter':'10000', 'squelch':'-50.0', 'description':'Blackstrap Repeater'},
    {'frequency':'146880000', 'mode':'FM', 'filter':'10000', 'squelch':'-50.0', 'description':'88 Linked Repeater'},
    {'frequency':'119750000', 'mode':'AM', 'filter':'10000', 'squelch':'-50.0', 'description':'PWM Approach/Departure'},
    {'frequency':'120900000', 'mode':'AM', 'filter':'10000', 'squelch':'-50.0', 'description':'PWM Tower'},
    {'frequency':'119050000', 'mode':'AM', 'filter':'10000', 'squelch':'-50.0', 'description':'PWM ATIS'},
    {'frequency':'93100000', 'mode':'WFM_ST', 'filter':'160000', 'squelch':'-50.0', 'description':'Coast FM'}
    ]


class Interface(BoxLayout):
    pass

# This class is the main application layout, below we build the initial GUI with Kivy
class MainView(BoxLayout):
    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        self.storage = DictStore('storage.dict')
        self.stop = threading.Event()
        self.radioMain()

## Builds the main control view
    def radioMain(self):
        self.settings = Interface()
        self.containerStack = StackLayout(padding=10, spacing=5, size_hint=(1, 1))
        # create a stack layout for info display
        self.info = StackLayout(padding=10, spacing=5, size_hint=(1, None))


        # info display widgets
        self.freqStatusLbl = Label(text='', height=50, font_size=50, size_hint=(1, None), color=[77,77,77,1])
        self.sigStatusLbl = Label(text='', height=20, font_size=20, size_hint=(1, None))
        self.sqlStatusLbl = Label(text='', height=20, font_size=20, size_hint=(1, None))
        self.modeStatusLbl = Label(text='', height=20, font_size=20, size_hint=(1, None))
        #self.filStatusLbl = Label(text='', height=20, font_size=20, size_hint=(1, None))
        self.info.add_widget(self.freqStatusLbl)
        self.info.add_widget(self.sigStatusLbl)
        self.info.add_widget(self.sqlStatusLbl)
        self.info.add_widget(self.modeStatusLbl)
        #self.info.add_widget(self.filStatusLbl)
        self.pb = ProgressBar(max=100, height=40, size_hint=(.5, None))
        self.signalGraphAnchorLayout = AnchorLayout(anchor_x='center', anchor_y='center',size_hint=(1,None), padding=10, height=20)
        self.signalGraphAnchorLayout.add_widget(self.pb)
        self.info.add_widget(self.signalGraphAnchorLayout)


        # create the input layout
        self.input = StackLayout(padding=30, spacing=5,size_hint=(1,None))
        # create the layout area where freq input will go
        self.freqBox = BoxLayout(spacing=10, height=100, size_hint=(1, None))
        self.freqTxt = TextInput(height=35, multiline=False, size_hint=(.7, None), font_size=20)
        # bind an action to hitting enter (on_text_validate) while in the frequency input fields
        self.freqTxt.bind(on_text_validate=self.freqSet)
        self.newFreqVal = None
        # add the freq input fields to the freq input box
        self.freqBox.add_widget(self.freqTxt)
        # create freq mode MHz or KHz dropdown
        self.freqModeDropdown = DropDown()
        self.freqModeMhzBtn = Button(text='MHz', size_hint_y=None, height=44)
        self.freqModeMhzBtn.bind(on_release=lambda btn: self.freqModeDropdown.select(self.freqModeMhzBtn.text))
        self.freqModeDropdown.add_widget(self.freqModeMhzBtn)
        self.freqModeKhzBtn = Button(text='Khz', size_hint_y=None, height=44)
        self.freqModeKhzBtn.bind(on_release=lambda btn: self.freqModeDropdown.select(self.freqModeKhzBtn.text))
        self.freqModeDropdown.add_widget(self.freqModeKhzBtn)
        self.freqModeBtn = Button(text='MHz', size_hint=(.1, None), height=35)
        self.freqModeBtn.bind(on_release=self.freqModeDropdown.open)
        self.freqModeDropdown.bind(on_select=lambda instance, x: setattr(self.freqModeBtn, 'text', x))
        self.freqBox.add_widget(self.freqModeBtn)

        # create the layout area where squelch will go
        self.sqlBox = BoxLayout(padding=10, spacing=20, height=55, size_hint=(1, None))
        # create squelch slider
        self.sqlSld = Slider(min=-150, max=0, value=0, size_hint=(.8, None), height=35, step=.5, cursor_size=[25,25])
        self.sqlSld.bind(value=self.sqlSet)
        self.newSqlVal = None  
        # squelch label and value label
        self.sqlLbl = Label(text='Squelch', height=35, size_hint=(.1, 1))
        self.sqlValLbl = Label(text=str(round(0, 2)) + ' dB', height=35, size_hint=(.1, 1))
        self.sqlBox.add_widget(self.sqlLbl)
        self.sqlBox.add_widget(self.sqlSld)
        self.sqlBox.add_widget(self.sqlValLbl)

        # Create mode button dropdown buttons and bindings
        self.dropdown = DropDown()
        self.fmBtn = Button(text='FM Narrow', size_hint_y=None, height=44)
        self.fmBtn.bind(on_release=lambda btn: self.dropdown.select(self.fmBtn.text))
        self.dropdown.add_widget(self.fmBtn)
        self.wfmsBtn = Button(text='FM Wide - Stereo', size_hint_y=None, height=44)
        self.wfmsBtn.bind(on_release=lambda btn: self.dropdown.select(self.wfmsBtn.text))
        self.dropdown.add_widget(self.wfmsBtn)
        self.wfmmBtn = Button(text='FM Wide - Mono', size_hint_y=None, height=44)
        self.wfmmBtn.bind(on_release=lambda btn: self.dropdown.select(self.wfmmBtn.text))
        self.dropdown.add_widget(self.wfmmBtn)
        self.amBtn = Button(text='AM', size_hint_y=None, height=44)
        self.amBtn.bind(on_release=lambda btn: self.dropdown.select(self.amBtn.text))
        self.dropdown.add_widget(self.amBtn)
        self.lsbBtn = Button(text='LSB - Lower Side Band', size_hint_y=None, height=44)
        self.lsbBtn.bind(on_release=lambda btn: self.dropdown.select(self.lsbBtn.text))
        self.dropdown.add_widget(self.lsbBtn)
        self.usbBtn = Button(text='USB - Upper Side Band', size_hint_y=None, height=44)
        self.usbBtn.bind(on_release=lambda btn: self.dropdown.select(self.usbBtn.text))
        self.dropdown.add_widget(self.usbBtn)
        self.cwlBtn = Button(text='CW-L', size_hint_y=None, height=44)
        self.cwlBtn.bind(on_release=lambda btn: self.dropdown.select(self.cwlBtn.text))
        self.dropdown.add_widget(self.cwlBtn)
        self.cwuBtn = Button(text='CW-U', size_hint_y=None, height=44)
        self.cwuBtn.bind(on_release=lambda btn: self.dropdown.select(self.cwuBtn.text))
        self.dropdown.add_widget(self.cwuBtn) 
        self.wfmoirtBtn = Button(text='WFM (oirt)', size_hint_y=None, height=44)
        self.wfmoirtBtn.bind(on_release=lambda btn: self.dropdown.select(self.wfmoirtBtn.text))
        self.dropdown.add_widget(self.wfmoirtBtn)
        self.rawBtn = Button(text='Raw I/Q', size_hint_y=None, height=44)
        self.rawBtn.bind(on_release=lambda btn: self.dropdown.select(self.rawBtn.text))
        self.dropdown.add_widget(self.rawBtn)
        self.offBtn = Button(text='Demodulation Off', size_hint_y=None, height=44)
        self.offBtn.bind(on_release=lambda btn: self.dropdown.select(self.offBtn.text))
        self.dropdown.add_widget(self.offBtn)
        self.modeBtn = Button(text='Demodulation Mode', size_hint=(1, None), height=35)
        self.modeBtn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: self.modeChange(x))
        self.newModeVal = None
        self.bmDropdown = DropDown()
        for bookmark in bookmarks:
            bmBtn = Button(text=bookmark['description'], size_hint_y=None, height=44)
            bmBtn.bind(on_release=lambda bmBtn: self.bmDropdown.select(bmBtn.text))
            self.bmDropdown.add_widget(bmBtn)
        self.bookmarkBtn = Button(text='Bookmarks', size_hint=(1, None), height=35)
        self.bookmarkBtn.bind(on_release=self.bmDropdown.open)
        self.bmDropdown.bind(on_select=lambda instance, x: self.bookmarkSelect(x))
        # add each widget to the login base layout 
        self.input.add_widget(self.freqBox)
        self.input.add_widget(self.sqlBox)
        self.input.add_widget(self.modeBtn)
        self.input.add_widget(self.bookmarkBtn)
        self.input.add_widget(self.settings)
        # add the login base layout to the main layout
        self.containerStack.add_widget(self.info)
        self.containerStack.add_widget(self.input)
        self.add_widget(self.containerStack)
        self.comErr = False
        self.startStatusUpdateThread(self)
        
        

    def bookmarkSelect(self, x):
        self.bookmarkBtn.text = x
        for bookmark in bookmarks:
            if bookmark['description'] == x:
                newFreq = bookmark['frequency']
                newMode = bookmark['mode']
                newSql = bookmark['squelch']
        self.newFreqVal = float(newFreq)
        self.newModeVal = newMode
        self.newSqlVal = float(newSql)
        

######### Status Update #########################################################################

    # this is is used to start the status update process, it gets the data immediately in a new thread and then starts the timer 
    def startStatusUpdateThread(self, touch):
        # send commands in new thread
        try:
            self.host = self.storage.get('hostip')['ip']
        except KeyError:
            msg('Key Error "ip"', 2)
            self.host = '127.0.0.1'
        try:
            self.port = self.storage.get('hostport')['port']
        except KeyError:
            msg('Key Error "port"', 2)
            self.port = '7356'
        try:
            self.interval = int(self.storage.get('interval')['interval'])
        except KeyError:
            msg('Key Error "port"', 2)
            self.interval = 1
        if self.comErr:
            self.interval = 1

        threading.Thread(target=self.getStatus, args=(touch,)).start()

    # this starts the status update timer in a new thread so we don't block the main kivy app loop 
    def startStatusUpdateTimer(self, touch):
        threading.Thread(target=self.updateTimer, args=(touch,)).start()

    # this is the actual timer always run in a separate thread
    def updateTimer(self, touch):
        time.sleep(self.interval)
        threading.Thread(target=self.startStatusUpdateThread, args=(touch,)).start()

    # this is the actual telnet com always run in a separate thread
    def getStatus(self, touch):
        # Get stored prefs
        try:
            self.status = {}
            tn = telnetlib.Telnet(self.host,self.port,1)
            if self.newFreqVal:
                setFreqCmd = 'F ' + str(self.newFreqVal)
                self.newFreqVal = None
                tn.write(setFreqCmd.encode('ascii') + b"\n")
                tn.read_until(b'\n', 3)
            if self.newSqlVal:
                setSqlCmd = 'L SQL ' + str(self.newSqlVal)
                self.newSqlVal = None
                tn.write(setSqlCmd.encode('ascii') + b"\n")
                tn.read_until(b'\n', 3)
            if self.newModeVal:
                setModeCmd = 'M ' + str(self.newModeVal)
                self.newModeVal = None
                tn.write(setModeCmd.encode('ascii') + b"\n")
                tn.read_until(b'\n', 3)
            tn.write(b"f\n")
            self.status['frequency'] = tn.read_until(b'\n', 3).decode('ascii').rstrip()
            tn.write(b"m\n")
            self.status['mode'] = tn.read_until(b"\n", 3).decode('ascii').rstrip()
            self.status['filter'] = tn.read_until(b"\n", 3).decode('ascii').rstrip()
            tn.write(b"l SQL\n")
            self.status['squelch'] = tn.read_until(b"\n", 3).decode('ascii').rstrip()
            tn.write(b"l STRENGTH")
            self.status['signal'] = tn.read_until(b"\n", 3).decode('ascii').rstrip()
            tn.close()
            self.comErr = False
        except socket.timeout:
            msg('Socket Timeout Error - The socket connection timed out', 1)
            self.status = {'frequency': '000000000','mode':'FM', 'squelch':'0', 'signal': '0'}
            self.comErr = True
        except ConnectionRefusedError:
            msg('Connection Refused - The connection was refused by the remote host. ', 2)
            self.status = {'frequency': '000000000','mode':'FM', 'squelch':'0', 'signal': '0'}
            self.comErr = True
        except EOFError:
            msg('EOF Error - The telnet connection raised an EOF exception. This error is not critical but may indicate a bug.', 1)
            self.status = {'frequency': '000000000','mode':'FM', 'squelch':'0', 'signal': '0'}
            self.comErr = True
        except ConnectionResetError:
            msg('Connection Reset - The connection was reset by the remote host.', 2)
            self.status = {'frequency': '000000000','mode':'FM', 'squelch':'0', 'signal': '0'}
            self.comErr = True
        self.onStatusResponse(self.status) # callback function (called when thread completes)

    @mainthread # this kivy wrapper ensures this function always runs in the main thread
    def onStatusResponse(self, touch):
        # print(self.status) ## DEBUG
        fMhz = str(float(self.status['frequency'])/1000000)
        ffMhz = fMhz[0:7]
        self.freqStatusLbl.text = ffMhz + ' MHz'
        self.sqlValLbl.text = self.status['squelch'] + ' dB'
        self.sqlStatusLbl.text = 'Squelch ' + self.status['squelch'] + ' dB'
        if self.newSqlVal == None:
            self.sqlSld.value = self.status['squelch']
        self.sigStatusLbl.text = 'Signal ' + self.status['signal'] + ' dB'
        self.pb.value = round(float(self.status['signal'])+100)
        mode = self.status['mode']
        if mode == 'FM': modeLabel = 'FM Narrow'
        if mode == 'WFM_ST': modeLabel = 'FM Wide - Stereo'
        if mode == 'WFM': modeLabel = 'FM Wide - Mono'
        if mode == 'AM': modeLabel = 'AM'
        if mode == 'LSB': modeLabel = 'LSB - Lower Side Band'
        if mode == 'USB': modeLabel = 'USB - Upper Side Band'
        if mode == 'CWL': modeLabel = 'CW-L'
        if mode == 'CWU': modeLabel = 'CW-U'
        if mode == 'WFM_ST_OIRT': modeLabel = 'WFM (oirt)'
        if mode == 'RAW': modeLabel = 'Raw I/Q'
        if mode == 'OFF': modeLabel = 'Demodulation Off'
        self.modeBtn.text = modeLabel
        self.modeStatusLbl.text = modeLabel
        if self.status['signal'] < self.status['squelch']:
            #print('signal')
            self.sigStatusLbl.color=[0,1,0,1]
        else:
            #print('no signal')
            self.sigStatusLbl.color=[1,0,0,1]
        try:
            if self.storage.get('connection')['connection'] == '1':
                self.startStatusUpdateTimer(self)
        except KeyError:
            msg('Key Error - "connection" - Com on/off setting value not found, proceeding with com on', 2)
            self.startStatusUpdateTimer(self)
        

######### END Status Update #########################################################################

######### Frequency #########################################################################

    def freqSet(self, x):
        self.newFreqVal = float(self.freqTxt.text)*1000000
        
######### END Frequency #########################################################################

######### Squelch #########################################################################

    def sqlSet(self, x, y):
        self.newSqlVal = y
        self.sqlValLbl.text = str(round(y,1)) + ' dB'

######### END Squelch #########################################################################

######### Modulation #########################################################################

    def modeChange(self, modeLabel):
        self.modeBtn.text = modeLabel
        if modeLabel == 'FM Narrow': mode = 'FM'
        if modeLabel == 'FM Wide - Stereo': mode = 'WFM_ST'
        if modeLabel == 'FM Wide - Mono': mode = 'WFM'
        if modeLabel == 'AM': mode = 'AM'
        if modeLabel == 'LSB - Lower Side Band': mode = 'LSB'
        if modeLabel == 'USB - Upper Side Band': mode = 'USB'
        if modeLabel == 'CW-L': mode = 'CWL'
        if modeLabel == 'CW-U': mode = 'CWU'
        if modeLabel == 'WFM (oirt)': mode = 'WFM_ST_OIRT'
        if modeLabel == 'Raw I/Q': mode = 'RAW'
        if modeLabel == 'Demodulation Off': mode = 'Off'
        self.newModeVal = mode

######### END Modulation #########################################################################

    # error/msg/log handling 
def msg(msg, lvl=1):
    if DEBUGLVL > 0 and lvl <= DEBUGLVL:
        if lvl == 1: print(f'ERROR - {msg}')
        if lvl == 2: print(f'WARN - {msg}')
        if lvl == 3: print(f'INFO - {msg}')
    
# This class builds and starts our app       
class gqrxremote(App):
    
    def on_stop(self):
        # The Kivy event loop is about to stop, so set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()
    
    def build(self):
        # self.settings_cls = SettingsWithSidebar # Optional alternative settings layout
        # self.use_kivy_settings = False
        self.mv = MainView()
        try:
            DEBUGLVL = self.mv.storage.get('debuglvl')['debuglvl']
        except KeyError:
            print('WARN - KeyError "debugLvl" - Debug level setting not found in storage')
        return self.mv

    def build_config(self, config):
        config.setdefaults("General", {"ip": "127.0.0.1", "port": "7356", "update": ".5", "connection":"1"})

    def build_settings(self, settings):
        settings.add_json_panel("Connection", self.config, data=json_settings)

    def on_config_change(self, config, section, key, value):
        if key == "ip":
            self.mv.storage.put('hostip', ip=value)
        elif key == "port":
            self.mv.storage.put('hostport', port=value)
        elif key == "update":
            self.mv.storage.put('interval', interval=value)
        elif key == "connection":
            self.mv.storage.put('connection', connection=value)
            if bool(value):
                self.mv.startStatusUpdateThread(self)

# this starts our kivy app and is the only main line code other than imports.
if __name__ == '__main__':
    gqrxremote().run()
