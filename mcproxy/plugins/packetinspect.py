from mcproxy.plugin import PacketFilter, plugin_manager
from bravo.packets import packets_by_name
import sys


# reverse the packets by name dict
packets_by_id = dict([(v, k) for (k, v) in packets_by_name.iteritems()])

class PacketInspect(PacketFilter):
    """
    Prints protocol information on the console.
    """

    def OnActivate(self):
        self.stdout = sys.stdout
        self.header = " T H I S   I S   A   B U G . "
        self.ignore = []

        # this will let us get every packet
        plugin_manager.register_listener(self, "packet")

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

    def publish(self, header, payload):
        if header not in self.ignore:
            write = self.stdout.write
            write("%s\n" % self.header)
            write("========== %s ===========\n" % packets_by_id[header])
            write(payload)

        return header, payload

