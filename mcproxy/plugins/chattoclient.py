from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import make_packet



class ChatToClient(Plugin):
    """
    Plugin publishes a resource that allows other plugins to send
    simple messages to the players client.

    registers resource "chat-to-client".  can be used as a normal output (has write).

    """

    def OnActivate(self):
        plugin_manager.register_resource("chat-to-client", ChatWrapper())


# wrap around the proxys connection to the client
class ChatWrapper(object):
    def __init__(self):
        self.output = None
        self.buffer = []

    def write(self, text):
        from mcproxy.protocol import client_proxy

        if client_proxy == None:
            self.buffer.append(text)
        else:
            self.output = client_proxy.transport
            [ self.the_real_write(text) for text in self.buffer ] 
            self.write = self.the_real_write
            self.the_real_write = None

    def the_real_write(self, text):
        """
        Send text back to the client as a chat packet.
        """

        for line in text.strip().split("\n"):
            line = line[:100]
            self.output.write(make_packet("chat", message=line))

