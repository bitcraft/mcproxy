from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import packets_by_name
import sys


# reverse the packets by name dict
packets_by_id = dict([(v, k) for (k, v) in packets_by_name.iteritems()])

class PacketInspect(Plugin):
    """
    Prints protocol information on the console.
    """

    requires = "PacketParser"

    def OnActivate(self):
        self.stdout = sys.stdout
        self.header = " T H I S   I S   A   B U G . "
        self.ignore = []

    def cmd_listen(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            return "packet %s is not recongized" % name
        else:
            plugin_manager.register_listener("packet-%s" % name)
            return "ok."

    def cmd_ignore(self, name):
        try:
            h = packets_by_name[name]
        except KeyError:
            return "packet %s is not recongized" % name
        else:
            plugin_manager.unregister_listener("packet-%s" % name)
            return "ok."

    def publish(self, header, payload):
        write = self.stdout.write
        write("%s\n" % self.header)
        write("========== %s ===========\n" % packets_by_id[header])
        write(payload)
        return header, payload

