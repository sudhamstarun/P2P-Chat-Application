#!/usr/bin/python3

# Student name and No.: Tarun Sudhams, 3035253876
# Student name and No.: Anchit Som, 3035244265
# Development platform: Mac OS X 10.12 and Ubuntu 18.04 LTS for testing
# Python version: Python 3.7.2 64-bit
# Version: 1.0


from tkinter import *
import sys
import socket
import time
import datetime
import threading
import _thread
#
# Global variables
#

client_status = "STARTED"  # status of the client as mentioned in the state diagrams
user_name =""  # Username defined by the user
currentRoom = ""  # name of the current
currentChatHashID = 0  # ID of the last message that was sent by the user
messageID = 0
# Global Lists adn Tuples
currentHashes = []
listOfMemeber = []
forwardLink = ()
backlinks = []
messages = []
lock = threading.Lock()

#
# This is the hash function for generating a unique
# Hash ID for each peer.
# Source: http://www.cse.yorku.ca/~oz/hash.html
#
# Concatenate the peer's username, str(IP address),
# and str(Port) to form a string that be the input
# to this hash function
#

def sdbm_hash(instr):
	hash = 0
	for c in instr:
		hash = int(ord(c)) + (hash << 6) + (hash << 16) - hash
	return hash & 0xffffffffffffffff

#Inspired from https://stackoverflow.com/questions/52928737/best-practice-to-vstack-multiple-large-np-arrays
def createChunker(array, chunkSize):
    return (array[pos:pos + chunkSize] for pos in range(0, len(array), chunkSize))

#
# Functions to handle user input
#

def do_User():
	global client_status
	if userentry.get():
		if client_status != "JOINED" and client_status != "CONNECTED":
			global username
			username = userentry.get()
			client_status = "NAMED"
			CmdWin.insert(1.0, "\n[User] username: "+username)
			userentry.delete(0, END)
		else:
			CmdWin.insert(1.0, "\nCannot change username after joining a chatroom!")
	else:
		CmdWin.insert(1.0, "\nPlease enter username!")

def do_List():
	message = "L::\r\n"
	try:
		roomServerSocket.send(message.encode("ascii"))
		recieveResponse = roomServerSocket.recv(1024)
		recieveResponse = str(recieveResponse.decode("ascii"))
		if recieveResponse:
			if recieveResponse[0] == 'G':
				recieveResponse = recieveResponse[2:-4]
				if len(recieveResponse) == 0:
					CmdWin.insert(1.0, "\nNo active chatrooms")
				else:
					rooms = recieveResponse.split(":")
					for room in rooms:
						CmdWin.insert(1.0, "\n\t"+room)
					CmdWin.insert(1.0, "\nHere are the active chat rooms:")
			elif recieveResponse[0] == 'F':
				recieveResponse = recieveResponse[2:-4]
				CmdWin.insert(1.0, "\nError fetching chatroom list: "+recieveResponse)
		else:
			raise socket.error("IndexError due to broken socket")
	except socket.error as err:
		print(str(err))
		CmdWin.insert(1.0, "\nConnection to Room Server broken, reconnecting;")
		roomServerSocket.close()
		_thread.start_new_thread (connectServer, (do_List, ))

def do_Join():
	global client_status
	try:
		if userentry.get():
			if username != "":
				if not (client_status == "JOINED" or client_status == "CONNECTED"):
					global room_name
					room_name = userentry.get()
					message = "J:"+room_name+":"+username+":"+myIP+":"+PortNumber+"::\r\n"
					roomServerSocket.send(message.encode("ascii"))
					recieveResponse = roomServerSocket.recv(1024)
					recieveResponse = str(recieveResponse.decode("ascii"))

					if recieveResponse:
						if recieveResponse[0] == 'M':
							recieveResponse = recieveResponse[2:-4]
							members = recieveResponse.split(":")

							global chatHashID
							chatHashID = members[0]

							global listOfMembers
							CmdWin.insert(1.0, "\nJoined chat room: "+room_name)
							for group in createChunker(members[1:], 3):
								listOfMembers.append(group)
								CmdWin.insert(1.0, "\n\t"+str(group))
							CmdWin.insert(1.0, "\nHere are the members:")
							client_status = "JOINED"
							userentry.delete(0, END)

							global currentRoom
							currentRoom = room_name
							_thread.start_new_thread (runForever, ())
							_thread.start_new_thread (runningServer, ())
							searchPeer(listOfMembers)
						elif recieveResponse[0] == 'F':
							recieveResponse = recieveResponse[2:-4]
							CmdWin.insert(1.0, "\nError performing JOIN req: "+recieveResponse)
					else:
						raise socket.error("IndexError due to broken socket")
				else:
					CmdWin.insert(1.0, "\nAlready joined/connected to another chatroom!!")
			else:
				CmdWin.insert(1.0, "\nPlease set username first.")
		else:
			CmdWin.insert(1.0, "\nPlease enter room name!")
	except socket.error as err:
		print(str(err))
		CmdWin.insert(1.0, "\nConnection to Room Server broken, reconnecting;")
		roomServerSocket.close()
		_thread.start_new_thread (connectServer, (do_Join, ))


def runForever():
	CmdWin.insert(1.0, "\nStarted KeepAlive Thread")
	while roomServerSocket:
		time.sleep(20)
		updatelistOfMembers("Keep Alive")
		if client_status == "JOINED" or not forwardLink:
			global listOfMembers
			searchPeer(listOfMembers)

def runningServer():
	sockfd = socket.socket()
	sockfd.bind( ('', int(PortNumber)) )
	while sockfd:
		sockfd.listen(5)
		isConnection, address = sockfd.accept()
		print ("Accepted connection from" + str(address))
		recieveResponse = isConnection.recv(1024)
		recieveResponse = str(recieveResponse.decode("ascii"))

		if recieveResponse:
			if recieveResponse[0] == 'P':
				recieveResponse = recieveResponse[2:-4]
				connectorInfo = recieveResponse.split(":")
				connectorRoomname = connectorInfo[0]
				connectorUsername = connectorInfo[1]
				connectorIP = connectorInfo[2]
				connectorPort = connectorInfo[3]
				connectorMsgID = connectorInfo[4]
				global listOfMembers
				try:
					memberIndex = listOfMembers.index(connectorInfo[1:4])
				except ValueError:
					if updatelistOfMembers("Server Procedure"):
						try:
							memberIndex = listOfMembers.index(connectorInfo[1:4])
						except ValueError:
							memberIndex = -1
							print("Unable to connect to " + str(address))
							isConnection.close()
					else:
						print("Unable to update member's list, so connection was rejected.")
						isConnection.close()
				if memberIndex != -1:
					message = "S:"+str(messageID)+"::\r\n"
					isConnection.send(message.encode("ascii"))
					concat = connectorUsername + connectorIP + connectorPort
					backlinks.append(((connectorInfo[1:4],sdbm_hash(concat)), isConnection))
					global client_status
					client_status = "CONNECTED"
					_thread.start_new_thread (peerManager, ("Backward", isConnection, ))
					CmdWin.insert(1.0, "\n" + connectorUsername + " has linked to me")
			else:
				isConnection.close()
		else:
			isConnection.close()

def peerManager(linkType, isConnection):
	while isConnection:
		recieveResponse = isConnection.recv(1024)
		recieveResponse = str(recieveResponse.decode("ascii"))

		if recieveResponse:
			if recieveResponse[0] == 'T':
				recieveResponse = recieveResponse[2:-4]
				msgInfo = recieveResponse.split(":")
				room = msgInfo[0]

				if room == currentRoom:
					originHashID = msgInfo[1]
					originUsername = msgInfo[2]
					originMsgID = msgInfo[3]
					originMsgLen = msgInfo[4]
					originMsg = recieveResponse[-(int(originMsgLen)):]

					lock.acquire()
					global messages
					if (originHashID, originMsgID) not in messages:
						MsgWin.insert(1.0, "\n["+originUsername+"] "+originMsg)
						messages.append((originHashID, originMsgID))
						lock.release()
						echoMessage(originHashID, originUsername, originMsg, originMsgID)
						arr = [member for member in currentHashes if str(member[1]) == str(originHashID) ]
						if not arr:
							print("Not found hash", str(arr))
							updatelistOfMembers("Peer Handler")
					else:
						print("Recvd repeated message")
						lock.release()
				else:
					print("Recvd message from wrong chat room")
		else:
			break

	if linkType == "Forward":
		updatelistOfMembers("Peer Quit")
		global forwardLink
		forwardLink = ()
		global client_status
		client_status = "JOINED"
		searchPeer(listOfMembers)

	else:
<<<<<<< HEAD
		global backlinks 
=======
		global backlinks
>>>>>>> f49e4d9cd4b31c40e27ba9421c1c084aedb3bbfc
		for back in backlinks:
			if back[1] == isConnection:
				backlinks.remove(back)
				break

def updatelistOfMembers(*source):
	message = "J:"+room_name+":"+username+":"+myIP+":"+PortNumber+"::\r\n"
	try:
		roomServerSocket.send(message.encode("ascii"))
		recieveResponse = roomServerSocket.recv(1024)
		recieveResponse = str(recieveResponse.decode("ascii"))
		if recieveResponse:
			if recieveResponse[0] == 'M':
				now = datetime.datetime.now()
				print(source, "Performing JOIN at", now.strftime("%Y-%m-%d %H:%M:%S"))
				recieveResponse = recieveResponse[2:-4]
				members = recieveResponse.split(":")
				global chatHashID
				if chatHashID != members[0]:
					global listOfMembers
					chatHashID = members[0]
					listOfMembers = []
					for group in createChunker(members[1:], 3):
						listOfMembers.append(group)
					print("Member list updated!")
					hashCalculator(listOfMembers)
				return True
			elif recieveResponse[0] == 'F':
				recieveResponse = recieveResponse[2:-4]
				CmdWin.insert(1.0, "\nError performing JOIN req: "+recieveResponse)
				return False
		else:
			return False
	except:
		CmdWin.insert(1.0, "\nConnection to Room Server broken, reconnecting;")
		roomServerSocket.close()
		_thread.start_new_thread (connectServer, (updatelistOfMembers, ))

def hashCalculator(listOfMembers):
	global currentHashes
	currentHashes = []
	for member in listOfMembers:
		concat = ""
		for info in member:
			concat = concat + info
		currentHashes.append((member,sdbm_hash(concat)))
		if member[0] == username:
			myInfo = member
	currentHashes = sorted(currentHashes, key=lambda tup: tup[1])
	return myInfo

def searchPeer(listOfMembers):
	myInfo = hashCalculator(listOfMembers)
	global currentHashes
	global myHashID

	myHashID = sdbm_hash(username+myIP+PortNumber)
	start = (currentHashes.index((myInfo, myHashID)) + 1) % len(currentHashes)

	while currentHashes[start][1] != myHashID:
		if [item for item in backlinks if item[0] == currentHashes[start]]:
			start = (start + 1) % len(currentHashes)
			continue
		else:
			peerSocket = socket.socket()
			try:
				peerSocket.connect((currentHashes[start][0][1], int(currentHashes[start][0][2])))
			except:
				print("Cannot make peer socket connection with ["+currentHashes[start][0][1]+"], trying another peer")
				start = (start + 1) % len(currentHashes)
				continue
			if peerSocket:
				if peerConnect(peerSocket):
					CmdWin.insert(1.0, "\nConnected via - " + currentHashes[start][0][0])
					global client_status
					client_status = "CONNECTED"
					global forwardLink
					forwardLink = (currentHashes[start], peerSocket)
					_thread.start_new_thread (peerManager, ("Forward", peerSocket, ))
					break
				else:
					peerSocket.close()
					start = (start + 1) % len(currentHashes)
					continue
			else:
				peerSocket.close()
				start = (start + 1) % len(currentHashes)
				continue
	if client_status != "CONNECTED":
		print("Unable to find forward connection")

def peerConnect(peerSocket):
	message = "P:"+room_name+":"+username+":"+myIP+":"+PortNumber+":"+str(messageID)+"::\r\n"
	try:
		peerSocket.send(message.encode("ascii"))
		recieveResponse = peerSocket.recv(1024)
		recieveResponse = str(recieveResponse.decode("ascii"))
		if recieveResponse:
			if recieveResponse[0] == 'S':
				return True
			else:
				return False
	except:
		return False

def do_Send():
	if userentry.get():
		if client_status == "JOINED" or client_status == "CONNECTED":
			global messageID
			messageID += 1
			MsgWin.insert(1.0, "\n["+username+"] "+userentry.get())
			echoMessage(myHashID, username, userentry.get(), messageID)
		else:
			CmdWin.insert(1.0, "\nNot joined any chat!")
	userentry.delete(0, END)

def echoMessage(originHashID, username, message, messageID):
	message = "T:"+room_name+":"+str(originHashID)+":"+username+":"+str(messageID)+":"+str(len(message))+":"+message+"::\r\n"
	if forwardLink:
		if str(forwardLink[0][1]) != str(originHashID):
			forwardLink[1].send(message.encode("ascii"))
			sentTo.append(str(forwardLink[0][1]))

	for back in backlinks:
		if str(back[0][1]) != str(originHashID):
			back[1].send(message.encode("ascii"))
			sentTo.append(str(back[0][1]))
	#CmdWin.insert(1.0, "\nSent to " + str(sentTo))

def do_Quit():

	if roomServerSocket:
		roomServerSocket.close()
		print("Quit: Closed Socket to Room Server")
	if forwardLink:
		forwardLink[1].close()
		print("Quit: Closed Socket to Forward link - ", forwardLink[0][0][0])
	for back in backlinks:
		back[1].close()
		print("Quit: Closed Socket to Backward link - ", back[0][0][0])
	sys.exit(0)

def connectServer(callback):
	global roomServerSocket
	global roomServerIP
	global roomServerPort
	global myIP

	ButtonOne['state'] = 'disabled'
	ButtonTwo['state'] = 'disabled'
	ButtonThree['state'] = 'disabled'
	ButtonFour['state'] = 'disabled'

	iterator=0

	while True:
		iterator = iterator+1
		print("Trying to connect to Room Server")
		try:
			roomServerSocket = socket.socket()
			roomServerSocket.connect((roomServerIPAddress, int(roomServerPort)))
			myIP = roomServerSocket.getsockname()[0]
			CmdWin.insert(1.0, "\nConnected to Room Server!")
			ButtonOne['state'] = 'normal'
			ButtonTwo['state'] = 'normal'
			ButtonThree['state'] = 'normal'
			ButtonFour['state'] = 'normal'
			break
		except ConnectionRefusedError:
			roomServerSocket.close()
			CmdWin.delete(2.0, 3.0)
			CmdWin.insert(1.0, "\nCannot contact Room Server, will try again in some time (" + str(iterator) +")")
			time.sleep(5)
	callback()
def do_Poke():
	print("Press Poke")
#
# Set up of Basic UI
#

win=Tk()
win.title("MyP2PChat")

# Top Frame for Message display
topframe=Frame(win, relief = RAISED, borderwidth = 1)
topframe.pack(fill = BOTH, expand = True)
topscroll=Scrollbar(topframe)
MsgWin=Text(topframe, height = '15', padx = 5, pady = 5,
              fg="red", exportselection=0, insertofftime=0)
MsgWin.pack(side=LEFT, fill=BOTH, expand=True)
topscroll.pack(side=RIGHT, fill=Y, expand=True)
MsgWin.config(yscrollcommand=topscroll.set)
topscroll.config(command=MsgWin.yview)

# Top Middle Frame for buttons
topmidframe = Frame(win, relief=RAISED, borderwidth=1)
topmidframe.pack(fill=X, expand=True)
ButtonOne = Button(topmidframe, width='6', relief=RAISED,
                   text="User", command=do_User)
ButtonOne.pack(side=LEFT, padx=8, pady=8)
ButtonTwo = Button(topmidframe, width='6', relief=RAISED,
                   text="List", command=do_List)
ButtonTwo.pack(side=LEFT, padx=8, pady=8)
ButtonThree = Button(topmidframe, width='6', relief=RAISED,
                     text="Join", command=do_Join)
ButtonThree.pack(side=LEFT, padx=8, pady=8)
ButtonFour = Button(topmidframe, width='6', relief=RAISED,
                    text="Send", command=do_Send)
ButtonFour.pack(side=LEFT, padx=8, pady=8)
ButtonSix = Button(topmidframe, width='6', relief=RAISED,
                   text="Poke", command=do_Poke)
ButtonSix.pack(side=LEFT, padx=8, pady=8)
ButtonFive = Button(topmidframe, width='6', relief=RAISED,
                    text="Quit", command=do_Quit)
ButtonFive.pack(side=LEFT, padx=8, pady=8)

# Lower Middle Frame for User input
lowmidframe = Frame(win, relief=RAISED, borderwidth=1)
lowmidframe.pack(fill=X, expand=True)
userentry = Entry(lowmidframe, fg="blue")
userentry.pack(fill=X, padx=4, pady=4, expand=True)

# Bottom Frame for displaying action info
bottframe = Frame(win, relief=RAISED, borderwidth=1)
bottframe.pack(fill=BOTH, expand=True)
bottscroll = Scrollbar(bottframe)
CmdWin = Text(bottframe, height='15', padx=5, pady=5,
              exportselection=0, insertofftime=0)
CmdWin.pack(side=LEFT, fill=BOTH, expand=True)
bottscroll.pack(side=RIGHT, fill=Y, expand=True)
CmdWin.config(yscrollcommand=bottscroll.set)
bottscroll.config(command=CmdWin.yview)


if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("P2PChat.py <server address> <server port no.> <my port no.>")
		sys.exit(2)
	else:
		global roomServerIPAddress
		global roomServerPort
		global PortNumber

		roomServerIPAddress = sys.argv[1]
		roomServerPort = sys.argv[2]
		PortNumber = sys.argv[3]
		_thread.start_new_thread (connectServer, (do_User, ))		#Start a new thread runnning the server part of P2P
	win.mainloop()