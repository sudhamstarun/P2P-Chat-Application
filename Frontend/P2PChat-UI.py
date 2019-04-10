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
user_name  # Username defined by the user
currentRoom = ""  # name of the current
lastMessageID = 0  # ID of the last message that was sent by the user
roomServerSocket


# Global Lists adn Tuples
hashArray = []
listofMemeber = []
forwardLink = ()

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


def createChunks(array, sizeOfChunk):
    return (array[pos:pos + sizeOfChunk] for pos in range(0, len(array), sizeOfChunk))


def hashCalculator(listofMemeber):
    global currentHashes

    currentHashes = []

    for member in listofMemeber:
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
        response = roomServerSocket.recv(1024)

        if response:
            response[0] = "M"
            currentTime = datetime.datetime.now()
            print(source. "Joining conducted at", currentTime.strftime(("%Y-%m-%d %H:%M:%S")))
            response = response[2:-4]
            members = response.split(":")

            if currentChatHashID != members[0]:
                global listofMemeber
                currentChatHashID = members[0]
                listofMemeber = []

                for cluster in createChunks(members[1:], 3):
                    listofMemeber.append(cluster)

                print("List has been updated")
                hashCalculator(listofMemeber)
            elif response[0] == "F":
                response = response[2:-4]
                CmdWin.insert(
                    1.0, "\n There is an error in performing JOIN req" + response)
                return False
        else:
            return False
    except:
        CmdWin.insert(
            1.0, "\nRoom server connection is broken, trying to reconnect....")
        roomServerSocket.close()
        _thread.start_new_thread(roomServerSocket, (memberListUpdate, ))

    except:


def peerManager(linkType, isConnection):
    while isConnection:
        response = isConnection.recv(1024)
        response = str(response.decode('ascii'))

        if response[0] == 'T':
            response = response[2:-4]
            messageInfo = response.split(':')
            room = messageInfo[0]

            if room == currentRoom:
                sourceHashID = messageInfo[1]
                sourceUserName = messageInfo[2]
                sourceMessageID = messageInfo[3]
                sourceMessageLength = messageInfo[4]

                sourceMessage = response[-(int(sourceMessageLength))]

                lock.acquire()

                global messages

                if(sourceHashID, sourceMessageID) not in messages:
                    MsgWin.insert(1.0, "\n["+sourceUserName"]" + sourceMessage)
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
        searchPeer(listofMemeber)
    
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
        


def runProcedureForever():
    CmdWin.insert(1.0, "\Running forever proceudure....")
        while roomServerSocket:
            time.sleep(20)
            memberListUpdate("Keep Alive")

            if client_status == "JOINED" or not forwardLink:
                global listofMemeber
                searchPeer(listofMemeber)


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
            CmdWin.insert(1.0, "\nCannot connect to the Room Server right now, reconnecting in a while......(" + str(i) ")")
            time.sleep(5)

    callback()

#
# Functions that were already given to us
#


def do_User(client_status):
    """
    The function allows us to check for the username if the user has so entered and if not entered, it prompts for a new username from the user
    """
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
        receiveResponse str(receiveResponse.decode('ascii'))

        if receiveResponse:
            if receiveResponse[0] == "G":
                receiveResponse = ResourceWarning[2:-4]

                if len(receiveResponse) == 0:
                    CmdWin.insert(1.0, "\nNo Active Chatrooms available")

                else:
                    availableRooms = receiveResponse.split(":")
                    for room i availableRooms:
                        CmdWin.insert(1.0, "\n\t"+room)
                    CmdWin.insert(
                        1.0, "\nHere is the list of active chatrooms")
            elif receiveResponse[0] == "F":
                receiveResponse = receiveResponse[2:-4]
                CmdWin.insert(
                    1.0, "\nError in retreiving the chatroom list: "+receiveResponse)

        else:
            rasise socket.error("Socket is broken. Please try again. (IndexError)")
    except socket.error as err:
        print(str(err))
        CmdWin.insert(1.0, "\nReconnecting.........")
        roomServerSocket.close()
        _thread.start_new_thread(roomServerSocket, (do_List,))


def do_Join(client_status):
    # starting tryy except loop again

    global currentChatHashID
    global listofMemeber
    global currentRoom

    try:
        if userentry.get():
            if username != "":
                if not (client_status == "JOINED" or client_status == "CONNECTED"):
                    global room_name  # name of the room that the user will enter
                    # record user input of the room name
                    room_name = userentry.get()

                    message = "J:" + room_name + ":" + user_name + \
                        ":" + IPAdress + ":" + PortNumber + "::\r\n"
                    connectServer.send(msg.encode('ascii'))
                    response = roomServerSocket.recv(1024)
                    response = str(response.decode('ascii'))

                    if response:
                        if response[0] == 'M':
                            response = response[2:-4]
                            members = response.split(":")

                            currentChatHashID = members[0]
                            CmdWin.insert(1.0, "\n\t" + str(group))
                            client_status = "JOINED"
                            userentry.delete(0, END)

                            currentRoom = room_name
                            _thread.start_new_thread)(runProcedureForever, ())


def do_Send():
    CmdWin.insert(1.0, "\nPress Send")


def do_Poke():
    CmdWin.insert(1.0, "\nPress Poke")


def do_Quit():
    CmdWin.insert(1.0, "\nPress Quit")
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

    win.mainloop()
