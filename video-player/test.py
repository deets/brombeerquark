import os
import sys
import nanomsg
import time

socket = nanomsg.Socket(nanomsg.PAIR)
socket.connect("ipc:///tmp/sv")

command = sys.argv[1]
payload = "=%s" % (sys.argv[2]) if len(sys.argv) == 3 else ""

message = "%s%s" % (command, payload)
print "sending", message
socket.send(message)
