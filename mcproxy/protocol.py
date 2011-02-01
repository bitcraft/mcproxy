from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet import reactor
from mcproxy.plugin import plugin_manager
import sys

def info(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def error(text):
    print text

# these are exposed to allow plugins to write data directly
client_proxy = None
proxy_remote = None

# this handle traffic from the client
class MCClientProtocol(Protocol):
    def __init__(self, remote):
        self.remote_host, self.remote_port = remote

    def dataReceived(self, data):
        if self.remote:
            raw = "".join(plugin_manager.publish("raw", data))
            self.remote.transport.write(raw)

    def connectionMade(self):
        self.buffer = ""
        self.remote = None
        reactor.connectTCP(self.remote_host, self.remote_port, RemoteClientProxyFactory(self))

# this handles traffic to the client
class MCRemoteProtocol(Protocol):
    def __init__(self, remote):
        self.remote = remote

    def dataReceived(self, data):
        self.remote.transport.write(data)

class RemoteClientProxyFactory(ClientFactory):
    def __init__(self, caller):
        self.caller = caller

    def buildProtocol(self, addr):
        global proxy_remote

        conn = MCRemoteProtocol(self.caller)
        self.caller.remote = conn
        info("Connected.\n")

        proxy_remote = conn

        return conn

    def clientConnectionLost(self, connector, reason):
        error("Remote connection lost.\n")

    def clientConnectionFailed(self, connector, reason):
        error("Connection failed. Reason %s\n:" % reason)

class ClientProxyFactory(Factory):
    protocol = MCClientProtocol

    def __init__(self, remote):
        self.remote = remote

    def buildProtocol(self, addr):
        global client_proxy

        conn = self.protocol(self.remote)
        client_proxy = conn

        return conn
