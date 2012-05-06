#!/usr/bin/python
# This script is inspired by : http://www.navarin.de/projects/rbox/
# Website ans repository : https://github.com/bsaleil/rhythmbox-android-remote

#Copyright (C) 2009 Baptiste Saleil

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# TODO :
	# Socket : Close socket in a good way
	# Repeat : Not available with mpris interfaces
	# Library sync : Not yet implemented

import socket
import dbus

# DBus
playerPath = 'org.mpris.MediaPlayer2.Player'
bus = dbus.SessionBus()
rbox = bus.get_object( 'org.gnome.Rhythmbox3', '/org/mpris/MediaPlayer2')
player = dbus.Interface(rbox, playerPath)
playerPr = dbus.Interface(rbox, 'org.freedesktop.DBus.Properties')

# Get current IP
ipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ipsocket.connect(('www.google.com',0))
ip = ipsocket.getsockname()[0]
ipsocket.close();

# Server socket
port = 8484
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.settimeout(None)
server_socket.bind(("", port))
server_socket.listen(5)

# Welcome prints
print "Server is listening."
print "Host : " + ip
print "Port : " + str(port)
print "(Ctrl+C to quit)"

# Main loop
while 1:

	# Intercept keyboard interruption
	try:
		# Get action from device
		client_socket, address = server_socket.accept()
		received = client_socket.recv(512)
		action, var = received.split('/')
		
		if action != "all" : print action
		
		# Set new position
		if action == "seek" :
			current = playerPr.Get(playerPath,"Position")
			new = int(var)*1000000
			seekVal = new - current
			player.Seek(seekVal)
		
		# Enable/Disable shuffle mode
		if action == "shuffle" :
			current = playerPr.Get(playerPath, "Shuffle")
			if current == 0 :
				playerPr.Set(playerPath, "Shuffle", True)
			else :
				playerPr.Set(playerPath, "Shuffle", False)
		
		# Volume Up
		if action == "volumeUp" :
			current = playerPr.Get(playerPath, "Volume")
			playerPr.Set(playerPath, "Volume", current + 0.1)
		
		# Volume Down
		if action == "volumeDown" :
			current = playerPr.Get(playerPath, "Volume")
			playerPr.Set(playerPath, "Volume", current - 0.1)
		
		# Cover request
		if action ==  "coverImage" :
			meta = playerPr.Get(playerPath,"Metadata")
			if meta.has_key("mpris:artUrl") :
				path = str(meta["mpris:artUrl"])
				path = path[7:len(path)]
				cover = open(path)
				reply=cover.read()
				cover.close()
				client_socket.send(reply)
		
		# All informations about current song
		if action == "all": 
			status = playerPr.Get(playerPath,"PlaybackStatus")
			meta = playerPr.Get(playerPath,"Metadata")
			position = playerPr.Get(playerPath,"Position")/1000000
			artExists = "false";
			
			if meta.has_key("mpris:artUrl") :
				artExists = "true";
		
			ret = ""
			ret += status.lower() + "/"
			ret += meta["xesam:album"] + "/"
			ret += meta["xesam:artist"][0] + "/"
			ret += meta["xesam:title"] + "/"
			ret += str(position) + "/"
			ret += str(meta["mpris:length"] / 1000000) + "/"
			ret += str(artExists)
			
			client_socket.send(ret.encode('utf-8'))
		
		# Previous track
		if action == "prev":
			player.Previous()
		# Play/Pause action
		if action == "playPause":
			player.PlayPause()
		# Next track
		if action == "next":
			player.Next()
		
		client_socket.close()
		
	# End of the program
	except (KeyboardInterrupt, SystemExit):
		server_socket.close()
		break;
