import os
import sys
import nanomsg


socket = nanomsg.Socket(nanomsg.PAIR)
socket.connect("ipc:///tmp/sv")
if len(sys.argv) == 1:
    socket.send("quit")
else:
    socket.send("play=%s" % os.path.normpath(os.path.expanduser(sys.argv[1])))
