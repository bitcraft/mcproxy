from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import packets_by_name



class GameShell(Plugin):
    """
    Plugin to allow use of a shell inside the game.

    Chat messages beginning with escape_key are forwarded to the shell
    and will not be forwarded to the remote server.
    """

    required = ["PacketParser", "Shell", "ChatToClient"]
    listen   = "packet-chat"
    default_char = "#"

    def OnActivate(self):
        self.shell, output = plugin_manager.get_resources("shell", "chat-to-client")
        self.shell.add_output(output)
        self.chat_header = packets_by_name["chat"]
        self.escape_char = GameShell.default_char

    def publish(self, header, payload):
        if payload.message[0] == self.escape_char:
            # chat messages from minecraft's servers are unicode
            # our shell (cmd.py) cannot handle unicode
            self.shell.onecmd(str(payload.message[1:]))
            return None

        return header, payload

