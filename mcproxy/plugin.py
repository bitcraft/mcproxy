from yapsy.PluginManager import PluginManager as PM
from yapsy.PluginManager import logging
from yapsy.IPlugin import IPlugin

from types import StringType, ListType

class PluginManager(PM):
    def __init__(self, *args, **kwargs):
        super(PluginManager, self).__init__(*args, **kwargs)
        self.listeners = {}
        self.handlers = {}

    def register_type(self, t):
        self.listeners[t] = []

    def register_listener(self, plugin, t):
        try:
            self.listeners[t].append(plugin)
        except KeyError:
            print "Cannot set %s to listen for %s.  Data type is not known." % \
                (plugin, t)

    def publish(self, t, *args, **kwargs):
        """
        Send this information to our listeners.
        """
        if len(self.listeners[t]) == 0:
            return args

        return [ p.publish(*args, **kwargs) for p in self.listeners[t] ]

plugin_manager = PluginManager()


class Plugin(IPlugin):
    """
    This is the interface for plugins

    The simple interface allows them to be managed by a shell.
    """

    protected_variables = ["parent"]

    def __init__(self):
        self.is_activated = False

    def set(self, name, value):
        name = name.strip("-")

        if name == "enabled":
            return "Please use the function enable or disable."

        if name in self.protected_variables:
            return "Cannot change this value"

        try:
            getattr(self, name)
        except AttributeError:
            return "Cannot set %s.  Variable doesn't exist.\n" % name
        else:
            setattr(self, name, value)

    def get(self, name):
        name = name.strip("-")
        try:
            return str(getattr(self, name))
        except AttributeError:
            return "Cannot get %s.  Variable doesn't exist.\n" % name

    def check_requirements(self):
        if hasattr(self, "required") == False:
            return True


        missing = []
        not_activated = []
        ok = True

        if isinstance(self.required, StringType):
            req = [self.required]
        elif isinstance(self.required, ListType):
            req = self.required

        for plugin in req: 
            l = [p.plugin_object for p in plugin_manager.getAllPlugins() if p.name == plugin]
            if l == []:
                missing.append(plugin)
                continue

            for p in l: 
                if p.is_activated == False:
                    not_activated.append(plugin)

        if missing != []:
            ok = False
            for plugin in missing:
                print "Cannot load %s.  Required plugin %s is not loaded." % \
                    (self.__class__.__name__, plugin)
            
        if not_activated != []:
            ok = False
            for plugin in not_activated:
                print "Cannot load %s.  Required plugin %s is not activated." % \
                    (self.__class__.__name__, plugin)
           
        return ok
 
    def activate(self):
        if self.check_requirements() == False:
            return

        self.is_activated = True
        if hasattr(self, "OnActivate"):
            self.OnActivate()

class ProxyPlugin(Plugin):
    """
    These plugins are meant to be added to the proxy.

    They should offer at least one StreamPlugin for
    incoming or outgoing data.

    incoming = from the server
    outgoing = from the client

    """

    incoming_filter = None
    outgoing_filter = None 


class StreamFilter(Plugin):
    """
    Stream plugins operate on raw data.
    """

    def filter(self, data):
        """
        Data is direct from the socket if the plugin is enabled.
        Return the data you want to be sent instead.

        Honor self.enabled

        Make SURE to return data even if you dont actually change it.
        """
        raise NotImplementedError

class PacketFilter(Plugin):
    """
    PacketPlugins operate with parsed packets.

    Packets should follow conventions in the bravo library

    Instances wanting to recive packets must register themselves
    in order to get data.  This cuts down on header checks.
    """

    def filter(self, header, payload):
        """
        Expects a header and payload from a packet.
        Return the packet the packet you want to be sent (if any).
        Do not send raw data.

        Make SURE to return the payload even if you dont actually change it.
        """
        raise NotImplementedError

