"""The `vitamins.comms` package contains classes for convenient communications between
Python processes via websockets. This is useful for sending commands to your bot
interactively, or for having your bot send data out to another Python program.

Data is sent in the form of `Message` objects, each of which has three members:

* `id` is an integer that is unique to that message.
* `tag` is a string.
* `data` is any pickleable Python object.

The `id` is assigned for you when the message is sent. The `tag` and `data` are
specified by you when you send a message. I use the `tag` as a convenient identifier for
the type of message, e.g. command, status, query, etc. Finally, the `data` can be any
pickleable Python object. This could be a number, a string, `None` (in case the `tag` is
meaningful all by itself, a dictionary, or even a class instance (assuming the program
on the other end of the connection has the same class definition available).
"""
from collections import deque, namedtuple
from typing import Any, Optional
import io
import pickle
import socket
from time import monotonic as now


HOST: str = "localhost"
PORT: int = 16849
BUFFSIZE: int = 4096
DEFAULT_RATE: int = 5
NOCLIENT_SPAM_INTERVAL: int = 10


Message = namedtuple("Message", "id, tag, data")
# id is int, tag is str, data is anything.


class SocketQueue:
    """This is the base class for Host and Client, which should be used for
    communication over a socket. This class is not intended to be instantiated directly.
    """

    first_index: int

    def __init__(
        self,
        host: str = HOST,
        port_offset: int = 0,
        buffsize: int = BUFFSIZE,
        rate: int = DEFAULT_RATE,
    ):
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

    def _recv(self) -> None:
        """Read any available data from the socket, decode it, and put it into the
        incoming queue.
        """
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

    def _send(self) -> None:
        """Encode any data in the outgoing queue and send it to the socket."""
        if not self.connected or now() < self.next_send:
            return
        self.next_send += self.poll_interval
        buff = []
        while self.outq:
            msg_id, tag, data = self.outq.popleft()
            buff.append(pickle.dumps((msg_id, tag, data)))
        if buff:
            stream = b"".join(buff)
            self.endpoint.sendall(stream)

    def put(self, tag: str, data: Any = None) -> int:
        """Put (tag, data) into the queue. Return the index.
        """
        msg = (self.msg_index, tag, data)
        self.msg_index += 2
        self.outq.append(msg)
        self._send()
        return msg[0]

    def get(self) -> Optional[Message]:
        """Return the next incoming message, or None.
        """
        self._recv()
        if not self.inq:
            return None
        return self.inq.popleft()

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()


class Host(SocketQueue):
    first_index: int = 0

    def connect(self) -> bool:
        """Try to connect to a client. Return True if a connection was successfully
        made (or already existed), False if not. A return value of False is expected,
        e.g., when there is no client trying to connect.
        """
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
                    return True
                except (BlockingIOError, OSError):
                    pass
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            self.socket.listen(1)
        return self.connected


class Client(SocketQueue):
    first_index: int = 1

    def connect(self, timeout: float = 5) -> bool:
        """Try to connect to a host. Return True if a connection was successfully
        made (or already existed), False if not.
        """
        if not self.connected:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            try:
                self.socket.connect((self.host, self.port))
                self.connected = True
                self.socket.setblocking(False)
                self.endpoint = self.socket
            except ConnectionRefusedError:
                pass
        return self.connected
