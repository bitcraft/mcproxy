from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import packets_by_name
import sys


# reverse the packets by name dict
packets_by_id = dict([(v, k) for (k, v) in packets_by_name.iteritems()])

class PacketInspect(Plugin):
    """
    Prints protocol information on the console.
    """

    requires = ["PacketParser", "chat-to-client"]

    def OnActivate(self):
        self.client_output = plugin_manager.get_resource("chat-to-client")
        self.stdout = sys.stdout
        self.header = " T H I S   I S   A   B U G . "
        plugin_manager.register_listener(self, "packet-position")
        plugin_manager.register_listener(self, "packet-location")

    def cmd_listen(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            self.client_output.write("packet \"%s\" is not recongized\n" % name) 
        else:
            plugin_manager.register_listener(self, "packet-%s" % name)
            self.client_output.write("ok.")

    def cmd_ignore(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            self.client.output.write("packet \"%s\" is not recongized" % name)
        else:
            plugin_manager.unregister_listener(self, "packet-%s" % name)
            self.client_output.write("ok.")

    def publish(self, header, payload):
        write = self.stdout.write
        write("========== %s ===========\n" % packets_by_id[header])
        write("%s\n" % str(payload))
        return header, payload

