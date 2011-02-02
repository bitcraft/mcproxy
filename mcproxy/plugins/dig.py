from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import packets as packet_def



class Dig(Plugin):
    required = "PacketParser"
    listen   = "packet-digging"
    public   = "multiplier"

    def OnActivate(self):
        self.multiplier = 20

    def publish(self, header, payload):
        if payload.state == 1:
            d = chr(header) + packet_def[header].build(payload)
            return d * int(self.multiplier)
