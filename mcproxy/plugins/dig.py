from mcproxy.plugin import Plugin, plugin_manager
from bravo.packets import make_packet



class Dig(Plugin):
    def OnActivate(self):
        plugin_manager.register_listener(self, "packet-digging")
        self.multiplier = 1

    def publish(self, header, payload):
        if payload.state == 1:
            d = make_packet(header, payload)
            return [d] * self.multiplier
