from mcproxy.plugin import Plugin, plugin_manager



class Raw(Plugin):
    """
    Plugin allows listeners to recieve "raw" data from a socket
    """
    def OnActivate(self):
        plugin_manager.register_type("raw")
