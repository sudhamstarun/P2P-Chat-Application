
# coding: utf-8

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

client_status = "START"  # status of the client as mentioned in the state diagrams
user_name =""  # Username defined by the user
currentRoom = ""  # name of the current
currentChatHashID = 0  # ID of the last message that was sent by the user
messageID = 0

 #variable for udp socket connection


# Global Lists adn Tuples
currentHashes = []
listofMember = []
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

#
# Functions to handle user input
#

#Inspired from https://stackoverflow.com/questions/52928737/best-practice-to-vstack-multiple-large-np-arrays
def createChunks(array, sizeOfChunk):
    return (array[pos:pos + sizeOfChunk] for pos in range(0, len(array), sizeOfChunk))


def hashCalculator(listofMember):
    global currentHashes

    currentHashes = []

    for member in listofMember:
        concat = ""
        for element in member:
            concat = concat + element
        currentHashes.append(member, sdbm_hash(concat))

        if member[0] == user_name:
            currentInfo = member

    currentHashes = sorted(currentHashes, key=lambda tuple: tuple[1])

    return currentInfo


def memberListUpdate(*source):
    global currentChatHashID
    msg = "J:" + room_name + ":" + user_name + \
        ":" + IPAddress + ":" + PortNumber + "::\r\n"

    try:
        roomServerSocket.send(msg.encode("ascii"))
        receiveResponse = roomServerSocket.recv(1024)

        if receiveResponse:
            receiveResponse[0] = "M"
            currentTime = datetime.datetime.now()
            print(source, "Joining conducted at", currentTime.strftime(("%Y-%m-%d %H:%M:%S")))
            receiveResponse = receiveResponse[2:-4]
            members = receiveResponse.split(":")

            if currentChatHashID != members[0]:
                global listofMember
                currentChatHashID = members[0]
                listofMember = []

                for cluster in createChunks(members[1:], 3):
                    listofMember.append(cluster)

                print("List has been updated")
                hashCalculator(listofMember)
            elif receiveResponse[0] == "F":
                receiveResponse = receiveResponse[2:-4]
                CmdWin.insert(
                    1.0, "\n There is an error in performing JOIN req" + receiveResponse)
                return False
        else:
            return False
    except:
        CmdWin.insert(
            1.0, "\nRoom server connection is broken, trying to reconnect....")
        roomServerSocket.close()
        _thread.start_new_thread(roomServerSocket, (memberListUpdate, ))


def peerConnect(peerSocket):
    msg = "P:"+room_name+":"+user_name+":"+IPAddress+":"+PortNumber+":"+str(messageID)+"::\r\n"
    try:
        peerSocket.send(msg.encode("ascii"))
        receiveResponse = peerSocket.recv(1024)
        receiveResponse = str(receiveResponse.decode("ascii"))
        if receiveResponse:
            if receiveResponse[0] == 'S':					#If peer responds with S, it is a success, so return True else false
                return True
            else:
                return False
    except:
        return False

def peerManager(linkType, isConnection):
    while isConnection:
        receiveResponse = isConnection.recv(1024)
        receiveResponse = str(receiveResponse.decode('ascii'))

        if receiveResponse[0] == 'T':
            response = receiveResponse[2:-4]
            messageInfo = receiveResponse.split(':')
            room = messageInfo[0]

            if room == currentRoom:
                sourceHashID = messageInfo[1]
                sourceUserName = messageInfo[2]
                sourceMessageID = messageInfo[3]
                sourceMessageLength = messageInfo[4]

                sourceMessage = receiveResponse[-(int(sourceMessageLength))]

                lock.acquire()

                global messages

                if(sourceHashID, sourceMessageID) not in messages:
                    MsgWin.insert(1.0, "\n["+sourceUserName+"]" + sourceMessage)
                    messages.append((sourceHashID, sourceMessageID))
                    lock.release()
                    echoMessage(sourceHashID, sourceUserName, sourceMessage, sourceMessageID)
                    memberArray = [member for member in currentHashes if str(member[1]) == str(sourceHashID)]

                    if not memberArray:
                        print("Hash not found", str(memberArray))
                        memberListUpdate("Peer Handler")

                else:
                    print("Received repeated message")
                    lock.release()
            else:
                print("Received message from wrong chat room")
        else:
            break

    if linkType == "Forward":
        memberListUpdate("Peer Quit")
        global forwardLink
        forwardLink = ()
        global client_status
        client_status="JOINED"
        searchPeer(listofMember)

    else:
        global backlinks
        for link in backlinks:
            if link[1] == isConnection:
                backlinks.remove(link)
                break

def runningServerLogic():
    sockfd = socket.socket()
    sockfd.bind(('', int(PortNumber)))

    while sockfd:
        sockfd.listen(5)
        isConnection, address = sockfd.accept()
        receiveResponse = isConnection.recv(1024)
        receiveResponse = str(receiveResponse.decode("ascii"))
        print ("Accepted connection from" + str(address))
        if receiveResponse:
            if receiveResponse[0] == 'P':
                receiveResponse = receiveResponse[2:-4]
                connectorInfo = receiveResponse.split(":")
                connectorUserName = connectorInfo[1]
                connectorMessageID = connectorInfo[4]
                connectorIP = connectorInfo[2]
                connectorPort = connectorInfo[3]
                connectorRoomName = connectorInfo[0]

                global listofMember

                try:
                    memberIndex = listofMember.index(connectorInfo[1:4])
                except ValueError:
                    if memberListUpdate("Server Procedure"):
                        try:
                            memberIndex = listofMember.index(connectorInfo[1:4])
                        except ValueError:
                            memberIndex = -1
                            print("Unable to connect to" + str(address))
                            isConnection.close()
                    else:
                        print("The connection was rejected as unable to update the members list")

                if memberIndex != -1:
                    msg = "S:" + str(messageID) + "::\r\n"
                    isConnection.send(msg.encode('ascii'))
                    join = connectorUserName + connectorIP + connectorPort
                    backlinks.append(((connectorInfo[1:4], sdbm_hash(join)), isConnection))

                    global client_status

                    client_status = "CONNECTED"
                    _thread.start_new_thread (peerManager, ("Backward", isConnection, ))
                    CmdWin.insrt(1.0, "\n" + connectorUserName + "has linked to me")

            else:
                isConnection.close()
        else:
            isConnection.close()

def runProcedureForever():
    CmdWin.insert(1.0, "\Running forever proceudure....")
    while roomServerSocket:
        time.sleep(20)
        memberListUpdate("Keep Alive")

        if client_status == "JOINED" or not forwardLink:
            global listofMember
            searchPeer(listofMember)

def searchPeer(listofMember):
    global currentHashes
    global currentHashID

    currentInfo = hashCalculator(listofMember)
    currentHashID = sdbm_hash(user_name+IPAddress+PortNumber)
    start = (hashes.index((currentInfo, currentHashID)) + 1)%len(currentHashes)

    while currentHashes[start][1] !=currentHashID:
        if [link for link in backlinks if link[0] == currentHashes[start]]:
            start = (start+1)%len(currentHashes)
            continue
        else:
            peerSocket = socket.socket()

            try:
                peerSocket.connect((currentHashes[start][0][1], int(currentHashes[start][0][2])))
            except:
                print("Peer socket connection failed with ["+currentHashes[start][0][1]+"], reconnecting...")
                start = (start+1)%len(currentHashes)
                continue
            if not peerSocket:
                peerSocket.close()
                start = (start+1)%len(currentHashes)
                continue

            else:
                if peerConnect(peerSocket):
                    CmdWin.insert(1.0, "\nConnected via - " + hashes[start][0][0])
                    global client_status
                    client_status = "CONNECTED"
                    global forwardLink
                    forwardLink = (currentHashes[start], peerSocket)
                    _thread.start_new_thread (peerManager, ("Forward", peerSocket, ))
                    break
                else:
                    peerSocket.close()
                    start = (start+1)%len(currentHashes)
                    continue

    if client_status != "CONNECTED":
        print("Cannot connect as forward connection not found")


def connectServer(callback):
    ButtonOne['state'] = 'disabled'
    ButtonTwo['state'] = 'disabled'
    ButtonThree['state'] = 'disabled'
    ButtonFour['state'] = 'disabled'

    iterator = 0

    global IPAddress
    global PortNumber
    global roomServerIPAddress
    global roomServerSocket

    while 1:
        iterator += 1
        print("Connecting to Room Server again")
        try:
            roomServerSocket = socket.socket()
            roomServerSocket.connect((roomServerIPAddress, int(PortNumber)))
            IPAddress = roomServerSocket.getsockname()[0]
            CmdWin.insert(1.0, "\nConnected to Room Server")
            ButtonOne['state'] = 'normal'
            ButtonTwo['state'] = 'normal'
            ButtonThree['state'] = 'normal'
            ButtonFour['state'] = 'normal'
            break
        except ConnectionRefusedError:
            roomServerSocket.close()
            CmdWin.delete(2.0, 3.0)
            CmdWin.insert(1.0, "\nCannot connect to the Room Server right now, reconnecting in a while......(" + str(i))
            time.sleep(5)

    callback()

def udp_listener():
    while True:
        inputmessage, address = udpsocket.recvfrom(1024)
        inputmessage = message.decode("utf-8")
        if inputmessage[0] == 'K':
            Acknowledgement = "A::\r\n"
            udpsocket.sendto(Acknowledgement.encode("ascii"), (address[0], address[1]))
            name=inputmessage.split(":")
            MsgWin.insert(1.0, "\nYou were poked by "+str(name[2]))


#
# Functions that were already given to us
#

def do_User():
    """
    The function allows us to check for the username if the user has so entered and if not entered, it prompts for a new username from the user
    """
    global client_status

    if userentry.get():  # to check if the entry inserted by the user is not empty
        # further the user should not have joined the chat room yet
        if client_status != "CONNECTED" and client_status != "JOINED":
            global user_name  # accessing the username
            user_name = userentry.get()
            client_status = "NAMED"
            CmdWin.insert(1.0, "\n[User] username: " + user_name)
            # upon storing the new value of username, delete the userentry
            userentry.delete(0, END)
        else:
            CmdWin.insert(
                1.0, "\nCannot change username after joining a chatroom")
    else:
        CmdWin.insert(1.0, "\nPlease enter your desired username")

        #create Udpsocket
    global udpsocket
    udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpsocket.bind(('', int(PortNumber)))
    udpthread = threading.Thread(target=udp_listener, daemon=True)
    udpthread.start()


def do_List():

    """
    When the end-user presses the [ List ] button, the system sends a LIST request to the Room server via a TCP connection. If the TCP connection hasn’t been established, the system initiates a connection to the Room server before sending the LIST request. The Room server should respond with the list of chatroom names (if any) or an error response if the server has experienced a problem in this interaction.
    """
    msg = "L::\r\n"
    # starting a try except condition
    try:
        roomServerSocket.send(msg.encode('ascii'))  # doing ascii encoding
        receiveResponse = roomServerSocket.recv(
            1024)  # storing the response received
        # converting the bytearray to string
        receiveResponse = str(receiveResponse.decode('ascii'))

        if receiveResponse:
            if receiveResponse[0] == "G":
                receiveResponse = receiveResponse[2:-4]

                if len(receiveResponse) == 0:
                    CmdWin.insert(1.0, "\nNo Active Chatrooms available")

                else:
                    availableRooms = receiveResponse.split(":")
                    for room in availableRooms:
                        CmdWin.insert(1.0, "\n\t"+room)
                    CmdWin.insert(
                        1.0, "\nHere is the list of active chatrooms")
            elif receiveResponse[0] == "F":
                receiveResponse = receiveResponse[2:-4]
                CmdWin.insert(
                    1.0, "\nError in retreiving the chatroom list: "+receiveResponse)

        else:
            raise socket.error("Socket is broken. Please try again. (IndexError)")
    except socket.error as err:
        print(str(err))
        CmdWin.insert(1.0, "\nReconnecting.........")
        roomServerSocket.close()
        _thread.start_new_thread(roomServerSocket, (do_List,))


def do_Join():
    # starting try except loop again

    global currentChatHashID
    global listofMember
    global currentRoom
    global client_status

    try:
        if userentry.get():
            if user_name != "":
                if not (client_status == "JOINED" or client_status == "CONNECTED"):
                    global room_name
                    room_name = userentry.get()

                    message = "J:" + room_name + ":" + user_name + \
                        ":" + IPAddress + ":" + PortNumber + "::\r\n"
                    roomServerSocket.send(message.encode('ascii'))
                    receiveResponse = roomServerSocket.recv(1024)
                    receiveResponse = str(receiveResponse.decode('ascii'))

                    if receiveResponse:
                        if receiveResponse[0] == 'M':
                            receiveResponse = receiveResponse[2:-4]
                            members = receiveResponse.split(":")

                            global currentChatHashID
                            global listofMember
                            currentChatHashID = members[0]
                            CmdWin.insert(1.0, "\nChat room joined succesfully : " + room_name)


                            for chunk in createChunks(members[1:], 3):
                                listofMember.append(chunk)
                                CmdWin.insert(1.0, "\n\t" + str(chunk))
                            CmdWin.insert(1.0, "\nList of members:")
                            client_status = "JOINED"
                            userentry.delete(0, END)
                            global currentRoom
                            currentRoom = room_name
                            _thread.start_new_thread (runProcedureForever, ())
                            _thread.start_new_thread (runningServerLogic, ())
                            searchPeer(listofMember)

                        elif receiveResponse[0]== "F":
                            receiveResponse[0] = receiveResponse[2:-4]
                            CmdWin.insert(1.0, "\n Error in joining: " + receiveResponse)
                    else:
                        raise socket.error("Broken socused index error")
                else:
                    CmdWin.insert(1.0, "\nAlready connected to a chat room ")
            else:
                CmdWin.insert(1.0, "\nPlease set username first.")
    except socket.error as err:
        print(str(err))
        CmdWin.insert(1.0, "\nConnection to Room Server broken, reconnecting;")
        roomServerSocket.close()
        _thread.start_new_thread (connectServer, (do_Join, ))


def do_Send():
    if userentry.get():
        if client_status == "JOINED" or client_status == "CONNECTED":
            global messageID
            messageID += 1
            MsgWin.insert(1.0, "\n["+user_name+"] "+userentry.get())
            echoMessage(currentHashID, user_name, userentry.get(), messageID)		#Call echoMessage with my details.
        else:
            CmdWin.insert(1.0, "\nNot joined any chat!")
    userentry.delete(0, END)


def do_Poke():
    pokeflag=False #checks if user has joined
    CmdWin.insert(1.0, "\nPress Poke")
    if client_status != "JOINED":
        CmdWin.insert(1.0, "\nJoin a room first")
        pokeflag=True    
    elif client_status == "JOINED" and userentry.get()=='':
        for chunk in createChunks(members[1], 3):
            listofMember.append(chunk)
            CmdWin.insert(1.0, "\n\t" + str(chunk[0])) #displays list of members
        CmdWin.insert(1.0, "\nTo whom do you want to send the poke?")
        flag=False
        for name in listofMember:
            if name[0] == userentry.get():
                flag=True
        if userentry.get() == user_name or flag==False:
            CmdWin.insert(1.0, "\nPoke error.")
        else:
            pokename = userentry.get() 	#poking client name
    else:
        pokename = userentry.get() #poking client name
        userentry.delete(0, END)

    if pokeflag==False:
        #poke function
        for name in listofMember:
            if name[0] == pokename:
                pokenameip=name[1] #poke client IP
                pokenameport=name[2] #poke client Port
        message = "K:" + room_name + ":" + user_name + "::\r\n"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket 
        sock.sendto(message.encode("ascii"), (pokenameip, pokenameport))
        sock.settimeout(2)
        try:
            _, _ = sock.recvfrom(1024)
            CmdWin.insert(1.0, "\nGot Acknowledgement.")
        except socket.timeout:
            print("Timeout! Try again.")
            CmdWin.insert(1.0, "\nDid not receive Acknowledgement.")
        sock.close()


def do_Quit():
    if roomServerSocket:
        roomServerSocket.close()
        print("Quit: Closed Socket to Room Server")
    if forwardLink:
        forwardLink[1].close()
        print("Quit: Closed Socket to Forward link - ", forwardLink[0][0][0])
    for link in backlinks:
        link[1].close()
        print("Quit: Closed Socket to Backward link - ", link[0][0][0])
    sys.exit(0)


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
