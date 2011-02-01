from mcproxy.plugin import PacketFilter, plugin_manager
from mcproxy.shell import ProxyShell
from bravo.packets import packets_by_name



class Shell(PacketFilter):
    """
    Plugin to allow use of a shell.

    Chat messages beginning with escape_key are forwarded to the shell
    and will not be forwarded to the remote server.
    """

    required = "PacketParser"
    default_char = "#"

    def OnActivate(self):
        self.shell = None
        self.chat_header = packets_by_name["chat"]
        self.escape_char = Shell.default_char
        plugin_manager.register_listener(self, "packet-chat")

    def publish(self, header, payload):
        from mcproxy.protocol import client_proxy
        self.shell = ProxyShell(stdout=client_proxy.transport)
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

