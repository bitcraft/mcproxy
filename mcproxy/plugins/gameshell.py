from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import packets_by_name, make_packet



class GameShell(Plugin):
    """
    Plugin to allow use of a shell inside the game.

    Chat messages beginning with escape_key are forwarded to the shell
    and will not be forwarded to the remote server.
    """

    required = ["PacketParser", "Shell"]
    listen   = "packet-chat"
    default_char = "#"

    def OnActivate(self):
        self.shell = plugin_manager.get_resource("shell")
        self.chat_header = packets_by_name["chat"]
        self.escape_char = GameShell.default_char

    def publish(self, header, payload):
        from mcproxy.protocol import client_proxy
        self.shell.add_output(ChatWrapper(client_proxy.transport))
        r = self.thereal_publish(header, payload)
        self.publish = self.thereal_publish
        self.thereal_publish = None
        return r

    def thereal_publish(self, header, payload):
        if payload.message[0] == self.escape_char:
            # chat messages from minecraft's servers are unicode
            # our shell (cmd.py) cannot handle unicode
            self.shell.onecmd(str(payload.message[1:]))
            return None

        return header, payload

# wrap around stdout
class ChatWrapper(object):
    def __init__(self, stdout):
        self.stdout = stdout

    def write(self, text):
        """
        Send text back to the client as a chat packet.
        """

        for line in text.strip().split("\n"):
            line = line[:100]
            self.stdout.write(make_packet("chat", message=line))
