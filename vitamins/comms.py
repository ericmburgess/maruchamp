"""Remote interaction for RamenBots.
"""

from collections import deque, namedtuple
import io
import pickle
import socket
from time import monotonic as now

from rlbot.matchcomms.client import MatchcommsClient
from rlbot.matchcomms.shared import JSON

HOST = "localhost"
PORT = 16849
BUFFSIZE = 4096
NOCLIENT_SPAM_INTERVAL = 10


Message = namedtuple("Message", "id, tag, data")
# id is int, tag is str, data is anything.


class SocketQueue:
    def __init__(self, host=HOST, port_offset=0, buffsize=BUFFSIZE, rate=5):
        self.host = host
        self.port = PORT + port_offset
        self.buffsize = buffsize
        self.inq, self.outq = deque(), deque()
        self.connected = False
        self.endpoint = None
        self.socket = None
        self.msg_index = self.first_index  # host uses evens, client uses odds
        self.poll_interval = 1 / rate
        self.next_poll = now()
        self.next_send = now()
        self.last_spam = -1e9

    def recv(self):
        if not self.connected or now() < self.next_poll:
            return
        self.next_poll += self.poll_interval
        data = []
        while True:
            try:
                data.append(self.endpoint.recv(BUFFSIZE))
            except BlockingIOError:
                break
        if data:
            stream = io.BytesIO(b"".join(data))
            while True:
                try:
                    info = pickle.load(stream)
                    msg = Message(*info)
                    self.inq.append(msg)
                except EOFError:
                    break

    def send(self):
        if not self.connected or now() < self.next_send:
            return
        self.next_send += self.poll_interval
        buff = []
        while self.outq:
            id, tag, data = self.outq.popleft()
            buff.append(pickle.dumps((id, tag, data)))
        if buff:
            stream = b"".join(buff)
            self.endpoint.sendall(stream)

    def put(self, tag, data=None):
        """Put (tag, data) into the queue. Return the index.
        """
        msg = (self.msg_index, tag, data)
        self.msg_index += 2
        self.outq.append(msg)
        self.send()
        return msg[0]

    def get(self):
        """Return the next incoming message, or None.
        """
        self.recv()
        if not self.inq:
            return None
        return self.inq.popleft()

    def close(self):
        if self.socket is not None:
            self.socket.close()


class Host(SocketQueue):
    first_index = 0

    def connect(self):
        """Try to connect to a client."""
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            self.socket.listen(1)
        if self.endpoint is None:
            if self.socket is not None:
                try:
                    self.endpoint, _ = self.socket.accept()
                    self.connected = True
                    print("[dev] Client connected.")
                    return
                except BlockingIOError:
                    if now() - self.last_spam > NOCLIENT_SPAM_INTERVAL:
                        print("[dev] No client... ")
                        self.last_spam = now()
                except OSError:
                    pass
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            self.socket.listen(1)


class Client(SocketQueue):
    first_index = 1

    def connect(self, timeout=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.socket.setblocking(False)
            self.endpoint = self.socket
            print("Connected to testing process.")
        except ConnectionRefusedError:
            print("Could not connect to testing process.")
        return self.connected

    def do(self, action="none"):
        return self.put("do", action)
