#!/usr/bin/env python

# [part of] a very special minecraft beta bot
# leif.theden@gmail.com

# special thanks to the bravo project!

from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet import reactor

from bravo.packets import packets_by_name, make_packet, parse_packets
from bravo.packets import packets as packet_def

from mcshell import ProxyShell

"""
this proxy works with an existing python/twisted setup.

put in information here, and connect to localhost on smp
just as you would another server.  data will be filtered
here and forwarded to the remote host defined here.

* if testing locally, do not forget that you cannot use
  the default port for your local server.  you should change
  the listening port on your minecraft server.
"""


# information on what server to connect to
remote_host = "127.0.0.1"
remote_port = 24565

# information on what to listen on
listen_port = 25565

def info(text):
    print text

def error(text):
    print text

# reverse the packets by name dict
packets_by_id = dict([(v, k) for (k, v) in packets_by_name.iteritems()])


class Plugin(object):
    """
    This is the interface for plugins

    The simple interface allows them to be managed by a shell.
    """

    def __init__(self):
        self._enabled = False
        self.parent = None

    def set(self, name, value):
        name = name.strip("-")
        try:
            getattr(self, name)
        except AttributeError:
            return "Cannot set %s.  Variable doesn't exist.\n" % name
        else:
            setattr(self, name, value)

    def get(self, name):
        name = name.strip("-")
        try:
            return str(getattr(self, name))
        except AttributeError:
            return "Cannot get %s.  Variable doesn't exist.\n" % name

    def enable(self):
        if self.parent == None:
            print "cannot enable %s.  parent is not set (this is a bug)." % self.__class__
        else:
            self._enabled = True

        # hook for when plugin is enabled
        if hasattr(self, "OnEnable"):
            self.OnEnable()

    def disable(self):
        self._endabled = False


class ProxyPlugin(Plugin):
    """
    These plugins are meant to be added to the proxy.

    They should offer at least one StreamPlugin for
    incoming or outgoing data.

    incoming = from the server
    outgoing = from the client

    """

    incoming_filter = None
    outgoing_filter = None 


class StreamFilter(Plugin):
    """
    Stream plugins operate on raw data.
    """

    def filter(self, data):
        """
        Data is direct from the socket if the plugin is enabled.
        Return the data you want to be sent instead.

        Honor self._enabled

        Make SURE to return data even if you dont actually change it.
        """
        raise NotImplementedError


class PacketFilter(Plugin):
    """
    PacketPlugins operate with parsed packets.

    Packets should follow conventions in the bravo library

    Instances wanting to recive packets must register themselves
    in order to get data.  This cuts down on header checks.
    """

    def filter(self, header, payload):
        """
        Expects a header and payload from a packet.
        Return the packet the packet you want to be sent (if any).
        Do not send raw data.

        Make SURE to return the payload even if you dont actually change it.
        """
        raise NotImplementedError

class ShellPlugin(PacketFilter):
    """
    Plugin to allow use of a shell.
    """

    def __init__(self, stdout, key):
        super(ShellPlugin, self).__init__()
        self.chat_header = packets_by_name["chat"]
        self.escape_key = key
        self.shell = ProxyShell(self, stdout)

    def OnEnable(self):
        self.parent.register(self, packets_by_name["chat"])

    def filter(self, header, payload):
        if self._enabled:
            if payload.message[0] == self.escape_key:
                # chat messages from minecraft's servers are unicode
                # our shell (cmd.py) cannot handle unicode
                # just convert it to plain ascii and remove the escape char
                self.shell.onecmd(str(payload.message[1:]))
                return None

        return header, payload

class PacketParser(StreamFilter):
    """
    Filters packets based on the bravo library's definitions.
    Packet Filters need to be added to this plugin.
    """

    def __init__(self):
        super(PacketParser, self).__init__()
        self.plugins = []
        self.buffer = ""
        self.interested = {}

    def register(self, plugin, header):
        try:
            assert plugin not in self.interested[header]
        except KeyError:
            self.interested[header] = []
            self.interested[header].append(plugin)
        except AssertionError:
            return
        else:    
            self.interested[header].append(plugin)
    
    def add_plugin(self, plugin):
        plugin.parent = self
        self.plugins.append(plugin)

    def remove_plugin(self, plugin):
        try:
            self.plugins.remove(plugin)
        except ValueError:
            pass
        else:
            plugin.parent = None

        for k, v in self.interested.values():
            try:
                v.remove(plugin)
            except ValueError:
                pass

    def filter(self, data):
        """
        Filter raw data and sends packets to the plugins attached.
        If the plugin returns a packet, it is added to the stream.
        If the plugin returns None, the packet is removed.

        Filters added to this one will need to be registered to get
        packets
        """

        if self._enabled:
            self.buffer += data
            packets, self.buffer = parse_packets(self.buffer)

            r = ""

            for header, payload in packets:
                try:
                    for f in self.interested[header]:
                        p = f.filter(header, payload)
                        if p != None:
                            r += chr(p[0]) + packet_def[p[0]].build(p[1])

                except KeyError:
                    r += chr(header) + packet_def[header].build(payload)

            return r
        else:
            return data

class PacketInspect(PacketFilter):
    def __init__(self, h):
        super(PacketInspect, self).__init__()
        self.stdout = sys.stdout
        self.header = h
        self.buffer = ""
        self.ignore = []

    def cmd_ignore(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            return "packet %s is not recongized" % name
        else:
            self.ignore.append(h)
            return "ok."

    def cmd_unignore(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            return "packet %s is not recongized" % name
        else:
            self.ignore.remove(h)
            return "ok."

    # this expects to use minecraft packets, not raw data
    def filter(self, header, payload):
        if self._enabled:
            if header not in self.ignore:
                write = self.stdout.write
                write("%s\n" % self.header)
                write("========== %s ===========\n" % packets_by_id[header])
                write(payload)

        return header, payload

# this handle traffic from the client
class MCClientProtocol(Protocol):
    def dataReceived(self, data):
        if self.remote:
            for p in self.plugins:
                data = p.filter(data)
            self.remote.transport.write(data)

    def add_plugin(self, plugin):
        self.plugins.append(plugin)
        plugin.parent = self

    def remove_plugin(self, plugin):
        try:
            self.plugins.remove(plugin)
        except ValueError:
            pass
        else:
            plugins.parent = None

    def connectionMade(self):
        self.plugins = []
        self.buffer = ""
        self.remote = None

        # setup our packet parser plugin
        parser = PacketParser()
        self.add_plugin(parser)
        parser.enable()

        # set up the shell plugin (goes the the packet parser)
        s = ShellPlugin(self.transport, "#")
        parser.add_plugin(s)
        s.enable()

        reactor.connectTCP(remote_host, remote_port, RemoteClientProxyFactory(self))

# this handles traffic to the client
class MCRemoteProtocol(Protocol):
    def __init__(self, remote):
        self.remote = remote
        self.plugins = []
        self.buffer = ""

    def dataReceived(self, data):
        self.remote.transport.write(data)

class RemoteClientProxyFactory(ClientFactory):
    def __init__(self, caller):
        self.caller = caller

    def buildProtocol(self, addr):
        conn = MCRemoteProtocol(self.caller)
        self.caller.remote = conn
        info("Connected.\n")
        return conn

    def clientConnectionLost(self, connector, reason):
        #self.caller.loseConnection()
        error("Remote connection lost.\n")

    def clientConnectionFailed(self, connector, reason):
        # bug: reason is a bit too detailed to send back to the client...
        error("Connection failed. Reason %s\n:" % reason)

class ClientProxyFactory(Factory):
    protocol = MCClientProtocol

if __name__ == "__main__":
    reactor.listenTCP(listen_port, ClientProxyFactory())
    reactor.run()
