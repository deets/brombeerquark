import os
import sys
import nanomsg
import time

socket = nanomsg.Socket(nanomsg.PAIR)
socket.connect("ipc:///tmp/sv")

if len(sys.argv) == 1:
    message = "quit"
else:
    message = "play=%s" % os.path.normpath(os.path.expanduser(sys.argv[1]))

time.sleep(3.0)
print "sending", message
socket.send(message)
