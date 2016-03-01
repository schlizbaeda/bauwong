#!/usr/bin/python3
# -*- coding: utf-8 -*-


#                 YAMuPlay - Yet Another Music Player
#                 Copyright (C) 2016  schlizbaeda
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License
# or any later version.
#             
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#
# This software uses the following modules:
# -----------------------------------------
#
# * python-omxplayer-wrapper                 LPGL v3
#   https://github.com/willprice/python-omxplayer-wrapper
#
# * pyudev v0.18                             LPGL v2.1
#   https://github.com/lunaryorn/pyudev.git
#
# * six V1.10.0                              free license
#   https://pypi.python.org/pypi/six
#
#
# These packages were adjusted especially for use with Python v3
#


import signal # notwendig, um richtig auf Strg+C (in der aufrufenden Konsole) zu reagieren
import os
import subprocess
import time
from omxplayer import OMXPlayer

# tkinter
import tkinter
import tkinter.ttk # wird in dieser Software nur für das Treeview-Steuerelement benötigt
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog

# Module für USB-detect-Ereignisse:
import pyudev




##### Funktionen für omxplayer-Aufruf #####
def updateButPlayPause():
    global gl_omxplayer
    if gl_omxplayer is None:
        playing = False
    else:
        playing = gl_omxplayer.playback_status() == "Playing"

    if  playing == True:
        butPlayPause.config(text = '||')
    else:
        butPlayPause.config(text = '>')
    try:
        bauwong.update() # DoEvents
    except:
        pass
    
def omxplayerRestart(file):
    global gl_omxplayer
    try:
        alpha = int(spinAlpha.get())
    except:
        alpha = 210
    if alpha > 255:
        alpha = 255
    elif alpha < 0:
        alpha = 0
    spinAlpha.delete(0, tkinter.END)
    spinAlpha.insert(0, alpha)
    # 1. Prüfen, ob omxplayer bereits läuft:
    if not gl_omxplayer is None:
        gl_omxplayer.stop()
        gl_omxplayer.quit()
        gl_omxplayer = None
        try:
            bauwong.update() # DoEvents
        except:
            pass
    # 2. Neue omxplayer-Instanz erstellen und die Wiedergabe der angegebenen Datei starten:
    playing = False
    starttim = time.time() # Vergangene Sekunden seit dem 01. Januar 1970
    while playing == False:
        # Diese Schleife ist notwendig, da der omxplayer manchmal
        # beim Start eines Titels "Zeile 67:  <pid> Abgebrochen" meldet.
        # In diesem Falle würde sofort zum übernächsten Titel gesprungen werden,
        # was für den unbedarften Benutzer nicht nachvollziehbar ist!
        gl_omxplayer = OMXPlayer(file, ['--alpha', str(alpha)])
        if gl_omxplayer is None:
            playing = False
        else:
            txt = gl_omxplayer.playback_status()
            playing = txt == "Playing" or txt == "Paused"
            gl_omxplayer.play()
            #gl_omxplayer.set_position(0.0) # Sofort mit voller Lautstärke beginnen, kein Fading!
        # Timeout berücksichtigen:    
        tim = time.time()
        if tim - starttim >= 2.5:
            playing = True # Schleife immer verlassen, wenn die Datei nach 2,5s immer noch nicht abgespielt wird
        time.sleep(0.1)
    updateButPlayPause()    
            
def omxplaylist():
    global gl_omxplayer, gl_omxplayerListindex, gl_omxplayerStopevent, gl_omxplayerPrevevent
    try:
        gl_omxplayerListindex = int(lstPlaylist.curselection()[0]) # nullbasierend
    except:
        gl_omxplayerListindex = -1000000 # WICHTIG: Nicht -1 verwenden, da bei rekursiven Aufrufen aufgrund von Ereignissen der Wert sonst schnell über 0 rutschen kann und dann fängt die Playlist von vorne an! 1000000 Klick-Ereignisse muss man als Anwender in kurzer Zeit erst mal schaffen :-)

    while gl_omxplayerListindex >= 0 and gl_quit == 0:
        print()
        print('Titel ' + str(gl_omxplayerListindex) + ': "' + lstPlaylist.get(gl_omxplayerListindex) + '"')
        omxplayerRestart('/media/' + lstPlaylist.get(gl_omxplayerListindex))
        playing = True
        while playing == True and gl_quit == 0:
            try:
                bauwong.update() # DoEvents
            except:
                pass
            time.sleep(0.05)
            try:
                txt = gl_omxplayer.playback_status()
                playing = txt == "Playing" or txt == "Paused"
            except:
                playing = True
        # Nächsten Eintrag aus der Playlist holen:
        lstPlaylist.select_clear(0, tkinter.END) # alle Markierungen löschen
        if gl_omxplayerPrevevent == True:
            gl_omxplayerPrevevent = False
        else:
            gl_omxplayerListindex += 1
        lstPlaylist.select_set(gl_omxplayerListindex)
        try:
            gl_omxplayerListindex = int(lstPlaylist.curselection()[0]) # nullbasierend
        except:
            gl_omxplayerListindex = -1000000 # WICHTIG: Nicht -1 verwenden, da bei rekursiven Aufrufen aufgrund von Ereignissen der Wert sonst schnell über 0 rutschen kann und dann fängt die Playlist von vorne an! 1000000 Klick-Ereignisse muss man als Anwender in kurzer Zeit erst mal schaffen :-)
        if gl_omxplayerStopevent == True:
            lstPlaylist.select_clear(0, tkinter.END) # alle Markierungen löschen
            gl_omxplayerListindex = -1000000 # WICHTIG: Nicht -1 verwenden, da bei rekursiven Aufrufen aufgrund von Ereignissen der Wert sonst schnell über 0 rutschen kann und dann fängt die Playlist von vorne an! 1000000 Klick-Ereignisse muss man als Anwender in kurzer Zeit erst mal schaffen :-)
    # Wenn das Programm hierher kommt, wurde die Playlist komplett abgespielt:
    gl_omxplayerStopevent = False # Merker für Stoptaste zurücksetzen
    gl_omxplayerPrevevent = False # Merker für |<<-Taste zurücksetzen
    if not gl_omxplayer is None:
        # Dieser if-Zweig wird nur ausgeführt, wenn diese def-Funktion aufgerufen wurde und die Playlist leer ist.
        gl_omxplayer.quit()
        gl_omxplayer = None
    updateButPlayPause() # Wenn die Playlist zu Ende ist, muss die Schaltfläche butPlayPause aktualisiert werden





##### Ereignishandler für omxplayer-Steuerung #####

# Teil 1: Schaltflächen analog zu einem CD-Player
def butPlayPause_Click(event):
    global gl_omxplayer, gl_omxplayerListindex
    print('butPlayPause.Click')
    if gl_omxplayer is None:
        # omxplayer läuft nicht:
        if len(lstPlaylist.curselection()) <= 0:
            # Wenn die Playlist abgeschlossen ist bzw. gerade nicht läuft, wird sie neu gestartet.
            # in der aktuellen Playlist ist nichts ausgewählt:
            lstPlaylist.select_set(0) # den ersten Titel auswählen
        omxplaylist()
    else:
        # omxplayer läuft:
        gl_omxplayer.play_pause()
        updateButPlayPause()


def butPrev_Click(event):
    global gl_omxplayer, gl_omxplayerListindex, gl_omxplayerPrevevent
    print('butPrev.Click')
    if gl_omxplayer is None:
        # omxplayer läuft nicht:
        if len(lstPlaylist.curselection()) <= 0:
            idx = int(lstPlaylist.size()) # letztes Element der Playlist wählen
        else:
            idx = int(lstPlaylist.curselection()[0])
        if idx > 0:
            idx -= 1
        lstPlaylist.select_clear(0, tkinter.END) # alle Markierungen löschen
        lstPlaylist.select_set(idx)
    else:
        # omxplayer läuft:
        gl_omxplayerPrevevent = True # bewirkt Berücksichtigung der |<<-Taste in der Funktion omxplaylist()
        if gl_omxplayer.position() <= 3.0:
            gl_omxplayerListindex -= 1
        gl_omxplayer.stop() # aktuellen Titel beenden (und in der Playlist fortfahren)
    if gl_omxplayerListindex < 0:
        gl_omxplayerListindex = 0


def butNext_Click(event):
    global gl_omxplayer
    print('butNext.Click')
    if gl_omxplayer is None:
        # omxplayer läuft nicht:
        if len(lstPlaylist.curselection()) <= 0:
            idx = -1 # erstes Element der Playlist wählen
        else:
            idx = int(lstPlaylist.curselection()[0])
        if idx < int(lstPlaylist.size()) - 1:
            idx += 1
        lstPlaylist.select_clear(0, tkinter.END) # alle Markierungen löschen
        lstPlaylist.select_set(idx)
    else:
        # omxplayer läuft:
        gl_omxplayer.stop() # aktuellen Titel beenden (und in der Playlist fortfahren)


def butRewind_ButtonPress(event): # entspricht Drücken der Taste
    global gl_omxplayerRewinding, gl_omxplayerForwarding
    print('butRewind.Press')
    gl_omxplayerRewinding = True
    gl_omxplayerForwarding = False
    starttim = time.time()
    delta = 0.5
    deltamax = 6.0 if gl_omxplayer is None else gl_omxplayer.duration() / 25
    if deltamax < 6.0: deltamax = 6.0 # mindestens 6 Sekunden springen
    while gl_omxplayerRewinding == True:
        if gl_omxplayer is None:
            # omxplayer läuft nicht:
            gl_omxplayerRewinding = False # while-Schleife beenden
        else:
            # omxplayer läuft:
            tim = time.time()
            if tim - starttim > 3.0:
                delta = deltamax 
            elif tim - starttim > 1.5:
                delta = 5.0
            elif tim - starttim > 0.75:
                delta = 1.5
            pos = gl_omxplayer.position() - delta
            if pos <= 0.0:
                pos = 0.0
                gl_omxplayerRewinding = False # while-Schleife beenden
            gl_omxplayer.set_position(pos)
            print('<< ' + str(delta))
            time.sleep(0.1)
            try:
                bauwong.update() # DoEvents
            except:
                pass
    
def butRewind_ButtonRelease(event): # entspricht Loslassen der Taste
    global gl_omxplayerRewinding, gl_omxplayerForwarding
    print('butRewind.Release')
    gl_omxplayerRewinding = False
    gl_omxplayerForwarding = False


def butForward_ButtonPress(event):# entspricht Drücken der Taste
    global gl_omxplayerRewinding, gl_omxplayerForwarding
    print('butForward.Press')
    gl_omxplayerRewinding = False
    gl_omxplayerForwarding = True
    starttim = time.time()
    delta = 0.5
    if gl_omxplayer is None:
        # omxplayer läuft nicht:
        duration = 0.0
        deltamax = 6.0
    else:
        # omxplayer läuft:
        duration = gl_omxplayer.duration() - 0.01 # Sprungziel minimal vor dem Ende der Mediendatei!
        deltamax = duration / 25
        if deltamax < 6.0: deltamax = 6.0 # mindestens 6 Sekunden springen
    while gl_omxplayerForwarding == True:
        if gl_omxplayer is None:
            # omxplayer läuft nicht:
            gl_omxplayerForwarding = False # while-Schleife beenden
        else:
            # omxplayer läuft:
            tim = time.time()
            if tim - starttim > 3.0:
                delta = deltamax 
            elif tim - starttim > 1.5:
                delta = 5.0
            elif tim - starttim > 0.75:
                delta = 1.5
            pos = gl_omxplayer.position() + delta
            if pos >= duration:
                # Hier muss überprüft werden, dass sich das Sprungziel
                # nicht hinter der Gesamtdauer des Titels befindet,
                # da sonst der omxplayer bei MP3-Dateien häufig nicht
                # mehr richtig reagiert.
                pos = duration
                gl_omxplayerForwarding = False # while-Schleife beenden
            gl_omxplayer.set_position(pos)
            print('>> ' + str(delta))
            time.sleep(0.1)
            try:
                bauwong.update() # DoEvents
            except:
                pass
    
def butForward_ButtonRelease(event): # entspricht Loslassen der Taste
    global gl_omxplayerRewinding, gl_omxplayerForwarding
    print('butForward.Release')
    gl_omxplayerRewinding = False
    gl_omxplayerForwarding = False


def butStop_Click(event):
    global gl_omxplayer, gl_omxplayerStopevent
    print('butStop.Click')
    if not gl_omxplayer is None:
        # omxplayer läuft:
        gl_omxplayerStopevent = True # bewirkt komplettes Ende der Playlist
        gl_omxplayer.stop()          # beendet die Wiedergabe des aktuellen Titels


# Teil 2: Steuerung über die Playlist

#def lstPlaylist_DblClick(event):
#    print('lstPlaylist.DblClick')
#    omxplaylist()
def lstPlaylist_Release(event): # --> Dient hier der Nachbildung eines toleranten Doppelklick-Ereignisses für Touchdisplays.
    # Im Release-Ereignis sind die Selektionen eines Listbox-Elementes aktuell,
    # was beim Button-Ereignis (Klick) noch nicht der Fall ist. Die Selektion
    # wird erst danach aktualisiert.
    global gl_lstPlaylistClickedItem, gl_lstPlaylistClickedTime
    #print('lstPlaylist.Click')
    try:
        bauwong.update() # DoEvents
    except:
        pass
    clickedTime = time.time()
    try:
        clickedItem = int(lstPlaylist.curselection()[0]) # nullbasierend
    except:
        clickedItem = -1
    if clickedItem >= 0 and clickedItem == gl_lstPlaylistClickedItem and clickedTime - gl_lstPlaylistClickedTime < 1.0:
        # die beiden letzten Klicks trafen das gleiche Listenelement innerhalb von 1 Sekunde:
        # Doppelklick!
        gl_lstPlaylistClickedItem = -1
        gl_lstPlaylistClickedTime = 0.0
        omxplaylist()
    else:
        # "erster" Klick: angeklicktes Element und Zeitpunkt merken
        gl_lstPlaylistClickedTime = clickedTime
        gl_lstPlaylistClickedItem = clickedItem
        
    



##### Ereignishandler des Treeview-Steuerelementes #####
##### und der Playlist ("Verschieben", "Löschen")  #####
def trvMediadir_Click(event): # --> Dient hier der Nachbildung eines toleranten Doppelklick-Ereignisses für Touchdisplays.
    global gl_trvMediadirClickedRow, gl_trvMediadirClickedTime
    try:
        bauwong.update() # DoEvents
    except:
        pass
    clickedTime = time.time()
    try:
        clickedRow = trvMediadir.identify_row(event.y)
    except:
        clickedRow = ''
    if clickedRow != '' and clickedRow == gl_trvMediadirClickedRow and clickedTime - gl_trvMediadirClickedTime < 1.0:
        # die beiden letzten Klicks trafen das gleiche Treeview-Element innerhalb von 1 Sekunde:
        # Doppelklick!
        for sel in trvMediadir.selection():
            # Fallunterscheidung 'dir' oder 'fil'
            if trvMediadir.tag_has('dir', sel) == True:
                # Verzeichnis (Directory):
                print(sel + ' is a directory.')
            else:
                # normale Datei:
                lstPlaylist.insert(tkinter.END, sel)
    else:
        # "erster" Klick: angeklicktes Element und Zeitpunkt merken
        gl_trvMediadirClickedTime = clickedTime
        gl_trvMediadirClickedRow = clickedRow

def recursiveGetAllChildren(trv, item = '', depth = 0):
    children = trv.get_children(item)
    for child in children:
        children += recursiveGetAllChildren(trv, child, depth + 1)
    return children

def butMediadirFind_Click(event):
    global gl_trvMediadirChanged, gl_trvMediadirList, gl_trvMediadirFoundChg, gl_trvMediadirFoundList, gl_trvMediadirFoundIndex
    find = entMediadirFind.get()
    if True:
        if gl_trvMediadirChanged == True: # Die USB-Laufwerke haben sich seit dem letzten Aufruf geändert
            gl_trvMediadirChanged = False
            gl_trvMediadirList = recursiveGetAllChildren(trvMediadir)
            gl_trvMediadirFoundChg = True # auch die Trefferliste muss angepasst werden!
        if gl_trvMediadirFoundChg == True: # Der Suchstring hat sich geändert
            gl_trvMediadirFoundChg = False
            gl_trvMediadirFoundList = [item for item in gl_trvMediadirList if find.lower() in item.lower()] # List Comprehension (pythontypisch und effektiv)
            gl_trvMediadirFoundIndex = 0
        if gl_trvMediadirFoundList != []: # auf nicht-leere Liste prüfen
            #print('gl_trvMediadirFoundList:')
            #for fnd in gl_trvMediadirFoundList:
            #    print('    ' + fnd)
            #print('gl_trvMediadirFoundIndex=' + str(gl_trvMediadirFoundIndex))
            #print('    ' + gl_trvMediadirFoundList[gl_trvMediadirFoundIndex])
            #print('')
            trvMediadir.see(gl_trvMediadirFoundList[gl_trvMediadirFoundIndex]) # aktuelle Fundstelle im Steuerelement zur Anzeige bringen (Baumstruktur öffnen und Element in den sichtbaren Bereich rücken)
            trvMediadir.selection_set(gl_trvMediadirFoundList[gl_trvMediadirFoundIndex].replace(' ', '\ ')) # aktuelle Fundstelle auswählen (selektieren): WICHTIG: Die Leerzeichen im Dateinamen müssen mit '\' "entwertet" werden, da sonst die Dateinamen "zerhackt" werden! Die resultierenden Teilstrings sind keine gültigen Einträge des Treeview-Steuerelementes
            gl_trvMediadirFoundIndex += 1
            if gl_trvMediadirFoundIndex >= len(gl_trvMediadirFoundList): gl_trvMediadirFoundIndex = 0
        else:
            gl_trvMediadirFoundIndex = -1 # nichts Passendes gefunden

def entMediadirFind_KeyPress(event):
    # Es wurde im Suchstring-Steuerelement eine Taste gedrückt:
    # Der Suchstring hat sich geändert!
    global gl_trvMediadirFoundChg
    #print('entMediadirFind_KeyPress:')
    #print('keysym="' + event.keysym + '"')
    #print('keycode=' + str(event.keycode))
    #print('keysym_num=' + str(event.keysym_num))
    #print('')
    if event.keysym_num == 65288 or event.keysym_num == 65535 or event.keysym_num < 65000:
        # Tasten "BackSpace" oder "Delete" oder normale Tasten
        #print('normale Taste')
        gl_trvMediadirFoundChg = True
    elif event.keysym_num == 65293 or event.keysym_num == 65421:
        # Tasten "Return" (bei den Buchstaben) oder "KP_Enter" (beim Ziffernblock)
        #print('ENTER')
        butMediadirFind_Click(event) # Suche durchführen
    else:
        # Tasten mit keysym_num >= 65000: Shift, Cursortasten, F-Tasten etc.
        #print('Sondertaste')
        pass


def butPlaylistRemove_Click(event):
    global gl_omxplayerListindex
    try:
        selIndex = int(lstPlaylist.curselection()[0]) # nullbasierend
    except:
        selIndex = -1
    if selIndex >= 0:
        # es ist ein Playlisteintrag selektiert:
        lstPlaylist.delete(selIndex)
        lstPlaylist.select_clear(0, tkinter.END) # alle Markierungen löschen
        lstPlaylist.select_set(selIndex)
        if selIndex <= gl_omxplayerListindex:            
            gl_omxplayerListindex -= 1

def butPlaylistMoveUp_Click(event):
    global gl_omxplayerListindex
    try:
        selIndex = int(lstPlaylist.curselection()[0]) # nullbasierend
    except:
        selIndex = -1
    if selIndex > 0:
        # es ist ein Playlisteintrag selektiert:
        selItem = lstPlaylist.get(selIndex)
        lstPlaylist.delete(selIndex)              # Ausgewählten Listeneintrag an der alten Stelle löschen
        lstPlaylist.insert(selIndex - 1, selItem) # den soeben gelöschten Listeneintrag davor wieder eintragen
        lstPlaylist.select_clear(0, tkinter.END)  # alle Markierungen löschen
        lstPlaylist.select_set(selIndex - 1)      # den verschobenen Listeneintrag selektieren
        if selIndex - 1 == gl_omxplayerListindex: # Der verschobene Listeneintrag drückte den aktuellen Titel um eine Position weiter: 
            gl_omxplayerListindex += 1            # --> mitziehen
        elif selIndex == gl_omxplayerListindex:   # Der verschobene Listeneintrag ist der aktuell laufende Titel: 
            gl_omxplayerListindex -= 1            # --> mitziehen
            
def butPlaylistMoveDn_Click(event):
    global gl_omxplayerListindex
    try:
        selIndex = int(lstPlaylist.curselection()[0]) # nullbasierend
    except:
        selIndex = -1
    if selIndex >= 0 and selIndex < lstPlaylist.size() - 1:
        # es ist ein Playlisteintrag selektiert:
        selItem = lstPlaylist.get(selIndex)
        lstPlaylist.delete(selIndex)              # Ausgewählten Listeneintrag an der alten Stelle löschen
        lstPlaylist.insert(selIndex + 1, selItem) # den soeben gelöschten Listeneintrag dahinter wieder eintragen
        lstPlaylist.select_clear(0, tkinter.END)  # alle Markierungen löschen
        lstPlaylist.select_set(selIndex + 1)      # den verschobenen Listeneintrag selektieren
        if selIndex + 1 == gl_omxplayerListindex: # Der verschobene Listeneintrag drückte den aktuellen Titel um eine Position weiter: 
            gl_omxplayerListindex -= 1            # --> mitziehen
        elif selIndex == gl_omxplayerListindex:   # Der verschobene Listeneintrag ist der aktuell laufende Titel: 
            gl_omxplayerListindex += 1            # --> mitziehen





##### Ereignishandler für "USB-detect", basierend auf dem Modul pyudev #####
def add_usbDrive(drive):
    #print('add USB drive "' + drive + '" from ' + gl_MediaDir)
    for base, dirs, files in os.walk(gl_MediaDir):
        base = base[len(gl_MediaDir):]  # Inhalt von gl_MediaDir ('/media') im Gesamtpfad vorne entfernen
        splitbase = base.split('/')     # TODO: os.path.sep() liefert das Pfad-Trennzeichen, unter LINUX '/'
        #print('base:  ', base)
        #print('split: ', splitbase)
        if base != '':
            if splitbase[1] == drive:
                #print('  add: ', splitbase[1:])
                insnode = ''
                for ins in splitbase[:-1]:
                    if insnode != '': insnode = insnode + '/'
                    insnode = insnode + ins
                nodeid = insnode
                if nodeid != '': nodeid = nodeid + '/'
                nodeid = nodeid + splitbase[-1] 
                #print('  ins: ', insnode)
                #print('  lst: ', splitbase[-1])
                #print('  nid: ', nodeid)
                trvMediadir.insert(insnode, 'end', nodeid, text = splitbase[-1], tags = ('dir', 'simple')) # Eintrag als Directory markieren
                for file in files:
                    trvMediadir.insert(nodeid, 'end', nodeid + '/' + file, text = file, tags = ('file', 'simple'))
                    #print('  nid: ', nodeid + '/' + file)
    gl_trvMediadirChanged = True

def remove_usbDrive(drive):
    #print('remove USB drive "' + drive + '"')
    trvMediadir.delete(drive)
    gl_trvMediadirChanged = True

def usb_eventhandler(usbdevice):
    # hier kann ohne Probleme eine Wartezeit oder etwas anderes Längeres eingefügt werden,
    # da diese Routine nicht im Hauptthread läuft, sondern in einem parallelen Thread.

    #print('\n#### {0} DEVICE ####'.format(usbdevice.action))
    #print('driver:       ' + ('None' if usbdevice.driver is None else usbdevice.driver))
    #print('sys_name:     ' + ('None' if usbdevice.sys_name is None else usbdevice.sys_name))
    #
    #print('\n#### Device ####')
    #print('action:      ' + usbdevice.action)
    #print('subsystem:   ' + usbdevice.subsystem)
    #print('driver:      ' + ('None' if usbdevice.driver is None else usbdevice.driver))
    #print('device_path: ' + usbdevice.device_path)
    #print('device_type: ' + ('None' if usbdevice.device_type is None else usbdevice.device_type))
    #print('device_node: ' + ('None' if usbdevice.device_node is None else usbdevice.device_node))
    #print('device_num:  ' + ('None' if usbdevice.device_type is None else usbdevice.device_type))
    #print('sys_path:    ' + ('None' if usbdevice.sys_path is None else usbdevice.sys_path))
    #print('sys_name:    ' + ('None' if usbdevice.sys_name is None else usbdevice.sys_name))
    #print('sys_n umber:  ' + ('None' if usbdevice.sys_number is None else usbdevice.sys_number))
    #print('tags:        ' + str(list(usbdevice.tags)))
    #print('sequ_number: ' + str(usbdevice.sequence_number))
    ##print('attributes:  ' + str(iter(usbdevice.attributes)))
    tim = time.time() # Vergangene Sekunden seit dem 01. Januar 1970
    starttim = tim
    curMediaDrives = os.listdir(gl_MediaDir)
    oldMediaDrives = curMediaDrives
    if usbdevice.action == 'add' and usbdevice.driver == 'usb-storage':
        cnt = 0
        while cnt < 10 and tim - starttim <= 9.0 and gl_quit == 0:
            time.sleep(0.2)
            tim = time.time() # Vergangene Sekunden seit dem 01. Januar 1970
            curMediaDrives = os.listdir(gl_MediaDir)
            if curMediaDrives == oldMediaDrives:
                cnt = 0
            else:
                cnt += 1
        if oldMediaDrives != curMediaDrives:
            time.sleep(0.2)
            # Die Directoryeinträge unter /media haben sich geändert (d.h. es ist ein neues USB-Laufwerk hinzugekommen)
            # neues Laufwerk unter /media ermitteln:
            for drive in curMediaDrives:
                if oldMediaDrives.count(drive) == 0:
                    add_usbDrive(drive)
    elif usbdevice.action == 'remove' and usbdevice.sys_name.find(':') >= 0:
        # Die Eigenschaft usbdevice.sys_name enthält das Zeichen ':',
        # wenn es sich um ein korrespondierendes remove-Ereignis
        # zu einem vorausgegangenem add-Ereignis mit usbdevice.driver == 'usb-storage' handelt.
        while curMediaDrives == oldMediaDrives and tim - starttim <= 3.0 and gl_quit == 0:
            time.sleep(0.2)
            tim = time.time() # Vergangene Sekunden seit dem 01. Januar 1970
            curMediaDrives = os.listdir(gl_MediaDir)
        if oldMediaDrives != curMediaDrives:
            # Die Directoryeinträge unter /media haben sich geändert (d.h. es ist ein neues USB-Laufwerk hinzugekommen)
            # entferntes Laufwerk unter /media ermitteln:
            for drive in oldMediaDrives:
                if curMediaDrives.count(drive) == 0:
                    remove_usbDrive(drive)
    # ENDE





##### Ereignishandler für die erweiterte Programmbedienung #####
def mnuFileOpen_Click():
        filename = tkinter.filedialog.askopenfilename(title = 'Playlist öffnen', filetypes = [('m3u-Playlist', '*.m3u'), ('Alle Dateien', '*')])
        if filename != '':
            try:
                file = open(filename, 'r')
            except IOError as err:
                tkinter.messagebox.showerror(title = 'Playlist öffnen', message = err)
            else:
                for line in file:
                    lstPlaylist.insert(tkinter.END, line.replace('\n', ''))
                file.close()
    
def mnuFileSave_Click():
    if lstPlaylist.get(0, tkinter.END) != (): # nur speichern, wenn die Playlist auch wirklich Einträge enthält
        filename = tkinter.filedialog.asksaveasfilename(title = 'Playlist speichern', initialfile = 'playlist.m3u', filetypes = [('m3u-Playlist', '*.m3u'), ('Alle Dateien', '*')])
        if filename != '':
            try:
                file = open(filename, 'w')
            except IOError as err:
                tkinter.messagebox.showerror(title = 'Playlist speichern', message = err)
            else:
                for line in lstPlaylist.get(0, tkinter.END):
                    file.write(line + '\n')
                file.close()

    
def mnuHelpAbout_Click():
    appName = 'YAMuPlay'
    appVer = '0.1'

    def mnuHelpAbout_OK():
        AboutBox.destroy()

    # GPL v3 - Kurzversion, falls Datei nicht lesbar:
    GPLv3 = '                YAMuPlay - Yet Another Music Player\n' + \
            '                Copyright (C) 2016  schlizbaeda\n' + \
            '\n' + \
            'This program is free software: you can redistribute it and/or modify\n' + \
            'it under the terms of the GNU General Public License as published by\n' + \
            'the Free Software Foundation, either version 3 of the License\n' + \
            'or any later version.\n' + \
            '\n' + \
            'This program is distributed in the hope that it will be useful,\n' + \
            'but WITHOUT ANY WARRANTY; without even the implied warranty of\n' + \
            'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n' + \
            'GNU General Public License for more details.\n' + \
            '\n' + \
            'You should have received a copy of the GNU General Public License\n' + \
            'along with this program. If not, see <http://www.gnu.org/licenses/>.\n'
    # GPL v3 vollständig aus Datei "bauwong.lic" einlesen:
    try:
        licfile = open('bauwong.lic')
    except:
        licfile = None
    if not licfile is None:
        GPLv3 = licfile.read()
        licfile.close()
    
    # modale AboutBox
    # Quelle: tkinter.unpythonic.net/wiki/ModalWindow
    AboutBox = tkinter.Toplevel()
    AboutBox.geometry('660x495')
    AboutBox.title('Info zu ' + appName + ' V' + appVer)
    titleFont = tkinter.font.Font(family = 'DejaVuSans', weight = 'bold', size = 16)
    normalFont = tkinter.font.Font(family = 'DejaVuSans', weight = 'normal', size = 12)
    monospaceFont = tkinter.font.Font(family = 'Monospace', weight = 'normal', size = 10)
    lblTitle = tkinter.Label(AboutBox, text = appName + ' V' + appVer, font = titleFont)
    lblTitle.pack(pady = 10)
    lblDesc1 = tkinter.Label(AboutBox, text = 'Yet Another Music Player           Version ' + appVer, font = normalFont)
    lblDesc1.pack()
    lblDesc2 = tkinter.Label(AboutBox, text = 'basierend auf omxplayer.bin, dem performanten MediaPlayer für den RaspberryPi', font = normalFont)
    lblDesc2.pack()
    lblDesc3 = tkinter.Label(AboutBox, text = '', font = normalFont)
    lblDesc3.pack()
    lblDesc4 = tkinter.Label(AboutBox, text = 'entwickelt von schlizbäda', font = normalFont)
    lblDesc4.pack()
    lblDesc5 = tkinter.Label(AboutBox, text = 'Copyright (C) 2016', font = normalFont)
    lblDesc5.pack()
    lblDesc6 = tkinter.Label(AboutBox, text = 'e-mail: schlizbaeda@gmx.de', font = normalFont)
    lblDesc6.pack()
    lblLic = tkinter.Label(AboutBox, text = '  Lizenz (GNU GPL v3):', font = normalFont)
    lblLic.pack(anchor = tkinter.W)
    txtLic = tkinter.Text(AboutBox, height = 16, width = 80, font = monospaceFont)
    txtLic.pack()
    txtLic.insert('1.0', GPLv3)
    butOK = tkinter.Button(AboutBox, text = '     OK     ', command = mnuHelpAbout_OK)
    butOK.pack(pady = 5)
    AboutBox.transient(bauwong)   # 1. Notwendigkeit für ein modales Fenster
    AboutBox.grab_set()           # 2. Notwendigkeit für ein modales Fenster
    bauwong.wait_window(AboutBox) # 3. Notwendigkeit für ein modales Fenster



        

##### Ereignishandler für Strg+C, "kill <Prozess-ID>" und Programm beenden ("Alt+F4") #####
# Programm über WM_DELETE_WINDOW beenden (z.B. durch Alt+F4 in der GUI oder Anklicken der Beenden-Schaltfläche mit dem "X"):
def onClosing():
    global gl_quit
    gl_quit = 1 # Merker setzen (1 = Programm wurde "normal" beendet)
    bauwong.quit()

# Programmabbruch durch Strg+C im aufrufenden Terminal:
def keyCtrl_C(signal, frame):
    global gl_quit
    gl_quit = 2 # Merker setzen (2 = Programm wurde über Ctrl+C im aufrufenden Terminal beendet)
    bauwong.quit()

# Programm über "kill <Prozess-ID>" beenden:
def terminateProcess(signal, frame):
    global gl_quit
    gl_quit = 4 # Merker setzen (4 = Programm wurde über "kill <Prozess-ID>" beendet)
    bauwong.quit()

# regelmäßiger Aufruf, damit Strg+C funktioniert:
def do_nothing():
    bauwong.after(200, do_nothing)





############ HAUPTPTOGRAMM ############        
# globale Variablen mit Vorbelegung:
gl_quit = 0                     # globaler Merker für andere Threads, wenn Ctrl+C oder Alt+F4 (Programm beenden) gedrückt wurde
gl_omxplayer = None             # Über dbus steuerbarer omxplayer
gl_omxplayerListindex = -1      # globale Variable für die Routine omxplaylist initialisieren
gl_omxplayerStopevent = False   # Merker für noch nicht verarbeitete Stoptaste
gl_omxplayerPrevevent = False   # Merker für noch nicht verarbeitete |<<-Taste
gl_omxplayerRewinding = False   # Merker für "Rewind"-Taste gedrückt
gl_omxplayerForwarding = False  # Merker für "Forward"-Taste gedrückt
gl_MediaDir = '/media'
gl_trvMediadirClickedRow = -1   # Nachbildung des Doppelklicks für Touchbildschirm
gl_trvMediadirClickedTime = 0.0 # Nachbildung des Doppelklicks für Touchbildschirm
gl_lstPlaylistClickedItem = -1  # Nachbildung des Doppelklicks für Touchbildschirm
gl_lstPlaylistClickedTime = 0.0 # Nachbildung des Doppelklicks für Touchbildschirm
gl_trvMediadirChanged = True    # für Titelsuche: True: Die Speichermedien (USB-Laufwerke) haben sich geändert und müssen daher für die Titelsuche neu eingelesen werden!
gl_trvMediadirList = []         # für Titelsuche: Liste initialisieren (leer), die später alle Titel enthält
gl_trvMediadirFoundChg = True   # für Titelsuche: True: Der Suchstring hat sich geändert
gl_trvMediadirFoundList = []    # für Titelsuche: Liste initialisieren (leer), die später alle Suchtreffer enthält
gl_trvMediadirFoundIndex = -1   # für Titelsuche: zuletzt gefundener Listeneintrag


# Quelle: www.tkdocs.com/tutorial/tree.html
bauwong = tkinter.Tk()
bauwong.title('Bauwong n.e.V.')
bauwong.geometry('1280x720')
dirFont = tkinter.font.Font(family = 'DejaVuSans', weight = 'bold', size = 12)
fileFont = tkinter.font.Font(family = 'DejaVuSans', weight = 'normal', size = 12)

# Menü erstellen:
mnuMainbar = tkinter.Menu(bauwong, font = fileFont)
mnuFile = tkinter.Menu(mnuMainbar, font = fileFont, tearoff = 0)
mnuFile.add_command(label = 'Playlist öffnen', command = mnuFileOpen_Click)
mnuFile.add_command(label = 'Playlist speichern', command = mnuFileSave_Click)
mnuHelp = tkinter.Menu(mnuMainbar, font = fileFont, tearoff = 0)
mnuHelp.add_command(label = 'Info', command = mnuHelpAbout_Click)
# Untermenüs in die oberste Menüleiste einhängen:
mnuMainbar.add_cascade(label = 'Datei', menu = mnuFile)
mnuMainbar.add_cascade(label = 'Hilfe', menu = mnuHelp)
# gesamte Menüleiste anzeigen:
bauwong.config(menu = mnuMainbar)


# Steuerelemente erstellen:
pwMainpane = tkinter.PanedWindow(bauwong, orient = 'horizontal', sashwidth = 16)
pwMainpane.pack(fill = 'both', expand = 'yes')

# linke Seite von pwMainpane:
# Treeview-Steuerelement, das alle USB-Laufwerke inkl. Verzeichnisstruktur auflistet und Dateisuche:
pwMediadir = tkinter.PanedWindow(pwMainpane, orient = 'vertical', sashwidth = 0)  # sashwidth=0: Breite der Trennlinie auf 0 setzen, damit sie nicht verschoben werden kann
pwMediadir.pack(fill = 'both', expand = 'yes')
trvMediadir = tkinter.ttk.Treeview(pwMediadir, show = 'tree') # show = 'tree': nur den Inhalt anzeigen, nicht die Überschriftsfeld(er) für die Spalten des Steuerelementes
#trvMediadir.font = fileFont # beißt nicht an!
frMediadirFind = tkinter.Frame(pwMediadir)
butMediadirFind = tkinter.Button(frMediadirFind, text = 'suchen')
butMediadirFind.place(x = 0, y = 10, width = 90, height = 30)
entMediadirFind = tkinter.Entry(frMediadirFind, text = 'Sepperich')
entMediadirFind.place(x = 100, y = 10, width = 400, height = 30)
pwMediadir.add(trvMediadir, minsize = 610) # Die Höhe (610 Pixel) des Playlist-Fensters ist hier auf eine Gesamthöhe von 720 Pixeln abgestimmt
pwMediadir.add(frMediadirFind)

# rechte Seite von pwMainpane:
# Listbox-Steuerelement mit Playlist und Schaltflächen für den Mediaplayer
pwPlayer = tkinter.PanedWindow(pwMainpane, orient = 'vertical', sashwidth = 0) # sashwidth=0: Breite der Trennlinie auf 0 setzen, damit sie nicht verschoben werden kann
pwPlayer.pack(fill = 'both', expand = 'no')



# Playlist und dazugehörige Schaltflächen "Verschieben" + "Entfernen"
pwPlaylist = tkinter.PanedWindow(bauwong, orient = 'horizontal', sashwidth = 0)  # sashwidth=0: Breite der Trennlinie auf 0 setzen, damit sie nicht verschoben werden kann
pwPlaylist.pack(fill = 'both', expand = 'yes')
lstPlaylist = tkinter.Listbox(pwPlaylist, font = fileFont, width = 160, selectmode = tkinter.BROWSE, xscrollcommand = True, yscrollcommand = True)
lstPlaylist.activate(1)
frPlaylistButtons = tkinter.Frame(pwPlaylist)
butPlaylistMoveUp = tkinter.Button(frPlaylistButtons, text = '^')
butPlaylistMoveUp.place(x = 10, y = 10, width = 30, height = 60)
#butPlaylistMoveUp.grid(column = 0, row = 0, sticky = tkinter.N)
butPlaylistRemove = tkinter.Button(frPlaylistButtons, text = 'X')
butPlaylistRemove.place(x = 10, y = 265, width = 30, height = 60)
#butPlaylistRemove.grid(column = 0, row = 1, sticky = tkinter.N)
butPlaylistMoveDn = tkinter.Button(frPlaylistButtons, text = 'v')
butPlaylistMoveDn.place(x = 10, y = 530, width = 30, height = 60)
#butPlaylistMoveDn.grid(column = 0, row = 2, sticky = tkinter.N)
pwPlaylist.add(lstPlaylist)
pwPlaylist.add(frPlaylistButtons, minsize = 50)

# Schaltflächen für Mediaplayer:
frPlayerbuttons = tkinter.Frame(pwPlayer)
butPlayPause = tkinter.Button(frPlayerbuttons)
butPlayPause.place(x = 0, y = 10, width = 90, height = 30)
updateButPlayPause()
butRewind = tkinter.Button(frPlayerbuttons, text = '<<')
butRewind.place(x = 100, y = 10, width = 90, height = 30)
butForward = tkinter.Button(frPlayerbuttons, text = '>>')
butForward.place(x = 200, y = 10, width = 90, height = 30)
butPrev = tkinter.Button(frPlayerbuttons, text = '|<<')
butPrev.place(x = 300, y = 10, width = 90, height = 30)
butNext = tkinter.Button(frPlayerbuttons, text = '>>|')
butNext.place(x = 400, y = 10, width = 90, height = 30)
butStop = tkinter.Button(frPlayerbuttons, text = 'Stop')
butStop.place(x = 500, y = 10, width = 90, height = 30)
lblAlpha = tkinter.Label(frPlayerbuttons, text = 'Transparenz:')
lblAlpha.place(x = 600, y = 10, width = 80, height = 30)
#spinAlpha = tkinter.Spinbox(frPlayerbuttons, values = (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255))
spinAlpha = tkinter.Spinbox(frPlayerbuttons, from_ = 0, to = 255, increment = 15)
spinAlpha.delete(0, tkinter.END) # Vorbelegung löschen
spinAlpha.insert(0, 210)         # und Startwert eintragen
spinAlpha.place(x = 690, y = 5, width = 60, height = 40)

pwPlayer.add(pwPlaylist, minsize = 610) # Die Höhe (610 Pixel) des Playlist-Fensters ist hier auf eine Gesamthöhe von 720 Pixeln abgestimmt
pwPlayer.add(frPlayerbuttons)


pwMainpane.add(pwMediadir)
pwMainpane.add(pwPlayer)











# Verzeichnis /media einlesen:
#print('USB-Laufwerke beim Start:')
trvMediadir.tag_configure('dir', font = dirFont)
trvMediadir.tag_configure('file', font = fileFont)
#trvMediadir.tag_configure('file', background = 'yellow')
for drive in os.listdir(gl_MediaDir):
    add_usbDrive(drive)




# Ereignishandler binden:
#trvMediadir.bind('<<TreeviewSelect>>', trvMediadir_TreeviewSelect) # funzt!
trvMediadir.bind('<Button-1>', trvMediadir_Click)
#trvMediadir.bind('<Double-1>', trvMediadir_DblClick)
entMediadirFind.bind('<KeyPress>', entMediadirFind_KeyPress)
butMediadirFind.bind('<Button-1>', butMediadirFind_Click)

#lstPlaylist.bind('<Button-1>', lstPlaylist_Click)
lstPlaylist.bind('<ButtonRelease>', lstPlaylist_Release)
#lstPlaylist.bind('<Double-1>', lstPlaylist_DblClick)
butPlaylistMoveUp.bind('<Button-1>', butPlaylistMoveUp_Click)
butPlaylistMoveDn.bind('<Button-1>', butPlaylistMoveDn_Click)
butPlaylistRemove.bind('<Button-1>', butPlaylistRemove_Click)
# Schaltflächen des Mediaplayers
butPlayPause.bind('<Button-1>', butPlayPause_Click)
butRewind.bind('<ButtonPress>', butRewind_ButtonPress)
butRewind.bind('<ButtonRelease>', butRewind_ButtonRelease)
butForward.bind('<ButtonPress>', butForward_ButtonPress)
butForward.bind('<ButtonRelease>', butForward_ButtonRelease)
butPrev.bind('<Button-1>', butPrev_Click)
butNext.bind('<Button-1>', butNext_Click)
butStop.bind('<Button-1>', butStop_Click)


# Ereignishandler für Strg+C, "kill <Prozess-ID>" und Programmende (Alt+F4) einrichten:
bauwong.protocol('WM_DELETE_WINDOW', onClosing) # normales Programmende
signal.signal(signal.SIGINT, keyCtrl_C)         # Abbruch durch Ctrl+C im aufrufenden Terminal
signal.signal(signal.SIGTERM, terminateProcess) # Abbruch durch "kill <Prozess-ID>"
# hier könnte man für alle SIG...-Signale, die standardmäßig zum Programmabbruch führen (also die meisten),
# ein Ereignis definieren, aber das lasse ich jetzt aus Performancegründen (und Faulheit) weg :-)
bauwong.after(200, do_nothing)

# USB-Ereignishandler einrichten:
context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('usb') # filtert nur die USB-Ereignisse
observer = pyudev.MonitorObserver(monitor, callback = usb_eventhandler, name = 'USB observer')
observer.daemon
observer.start()

# tkinter-Mainloop starten:
bauwong.mainloop()
observer.stop()
if not gl_omxplayer is None:
    # omxplayer läuft:
    gl_omxplayerStopevent = True # bewirkt komplettes Ende der Playlist
    gl_omxplayer.stop()          # beendet die Wiedergabe des aktuellen Titels
    gl_omxplayer.quit()          # Sauberes Beenden der noch vorhandenen omxplayer-Instanz beim Programmende
if gl_quit & 1:
    print('Das Programm wurde vom Anwender "normal" beendet.')
elif gl_quit & 2:
    print('Das Programm wurde über Ctrl+C im aufrufenden Terminalfenster abgebrochen.')
elif gl_quit & 4:
    print('Das Programm wurde über "kill <Prozess-ID>" beendet.')
else:
    print('Das Programm wurde auf unbekannte Weise beendet, gl_quit=' + str(gl_quit))
