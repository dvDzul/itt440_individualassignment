import socket
import sys
import time
import os
import struct
print "\nWelcome to the FTP server.\n\nTo get started, connect a client."
# Initialise socket stuff
TCP_IP = "192.168.56.103" # Only a local server
TCP_PORT = 8080  # Can be any number
BUFFER_SIZE = 1024 # Standard size
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()
print "\nConnected to by address: {}".format(addr)


def upld():
    # Send message once server is ready to recieve file details
    conn.send("1")
    # Receive file name length, then file name
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size)
    # Send message to let client know server is ready for document content
    conn.send("1")
    # Receive file size
    file_size = struct.unpack("i", conn.recv(4))[0]
    # Initialise and enter loop to recive file content
    start_time = time.time()
    output_file = open(file_name, "wb")
    # This keeps track of how many bytes we have received, so we know when to stop the loop
    bytes_recieved = 0
    print "\nReceiving..."
    while bytes_recieved < file_size:
        l = conn.recv(BUFFER_SIZE)
        output_file.write(l)
        bytes_recieved += BUFFER_SIZE
    output_file.close()
    print "\nRecieved file: {}".format(file_name)
    # Send upload performance details
    conn.send(struct.pack("f", time.time() - start_time))
    conn.send(struct.pack("i", file_size))
    return


def dwld():
    conn.send("1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    print file_name_length
    file_name = conn.recv(file_name_length)
    print file_name
    if os.path.isfile(file_name):
        # Then the file exists, and send file size
        conn.send(struct.pack("i", os.path.getsize(file_name)))
    else:
        # Then the file doesn't exist, and send error code
        print "File name not valid"
        conn.send(struct.pack("i", -1))
        return
    # Wait for ok to send file
    conn.recv(BUFFER_SIZE)
    # Enter loop to send file
    start_time = time.time()
    print "Sending file..."
    content = open(file_name, "rb")
    # Again, break into chunks defined by BUFFER_SIZE
    l = content.read(BUFFER_SIZE)
    while l:
        conn.send(l)
        l = content.read(BUFFER_SIZE)
    content.close()
    # Get client go-ahead, then send download details
    conn.recv(BUFFER_SIZE)
    conn.send(struct.pack("f", time.time() - start_time))
    return


def delf():
    # Send go-ahead
    conn.send("1")
    # Get file details
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length)
    # Check file exists
    if os.path.isfile(file_name):
        conn.send(struct.pack("i", 1))
    else:
        # Then the file doesn't exist
        conn.send(struct.pack("i", -1))
    # Wait for deletion conformation
    confirm_delete = conn.recv(BUFFER_SIZE)
    if confirm_delete == "Y":
        try:
            # Delete file
            os.remove(file_name)
            conn.send(struct.pack("i", 1))
        except:
            # Unable to delete file
            print "Failed to delete {}".format(file_name)
            conn.send(struct.pack("i", -1))
    else:
        # User abandoned deletion
        # The server probably recieved "N", but else used as a safety catch-all
        print "Delete abandoned by client!"
        return


def quit():
    # Send quit conformation
    conn.send("1")
    # Close and restart the server
    conn.close()
    s.close()
    os.execl(sys.executable, sys.executable, *sys.argv)


while True:
    # Enter into a while loop to recieve commands from client
    print "\n\nWaiting for instruction"
    data = conn.recv(BUFFER_SIZE)
    print "\nRecieved instruction: {}".format(data)
    # Check the command and respond correctly
    if data == "UPLD":
        upld()
    elif data == "DWLD":
        dwld()
    elif data == "DELF":
        delf()
    elif data == "QUIT":
        quit()
    # Reset the data to loop
    data = None
