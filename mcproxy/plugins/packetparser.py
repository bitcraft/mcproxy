from bravo.packets import packets as packet_def
from bravo.packets import packets_by_name, make_packet, parse_packets
from mcproxy.plugin import Plugin, plugin_manager

from types import StringType, ListType

# reverse the packets by name dict
packets_by_id = dict([(v, k) for (k, v) in packets_by_name.iteritems()])

class PacketParser(Plugin):
    """
    Filters packets based on the bravo library's definitions.
    Packet Filters need to be added to this plugin.
    """

    required = "Raw"
    listen   = "raw"

    def OnActivate(self):
        # this type will be published with every packet
        plugin_manager.register_type("packet")

        # register all the types we know from bravo
        for name in packets_by_name.keys():
            plugin_manager.register_type("packet-%s" % name)

        self.buffer = ""

    def publish(self, data):
        self.buffer += data
        packets, self.buffer = parse_packets(self.buffer)

        l = []
        for header, payload in packets:
            # send the packet to listeners of "packet-X"...they can choose what to listen for
            r = plugin_manager.publish("packet-%s" % packets_by_id[header], header, payload)
            l.append(r)

        r = ""
        for i in l:
            if isinstance(i, StringType):
                r += i
            elif i == [None]:
                continue
            # assume a list is a list of strings
            elif isinstance(i, ListType):
                r += "".join(i)
            else:
                r += chr(i[0]) + packet_def[i[0]].build(i[1])

        return r

