#!/usr/bin/env python

"""
[part of] a very special minecraft beta bot
leif.theden@gmail.com

this proxy works with an existing python/twisted setup.
bravo is required
"""

from mcproxy.protocol import ClientProxyFactory
from mcproxy.plugin import plugin_manager
from twisted.internet import reactor
import sys



# information on what server to connect to
remote_host = "127.0.0.1"
remote_port = 24565

# information on what to listen on
listen_port = 25565

def info(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def error(text):
    print text

print "Starting up..."
plugin_manager.setPluginPlaces(["/Users/leif/python-dev/mcproxy/plugins"])
plugin_manager.setPluginInfoExtension("plugin")
plugin_manager.collectPlugins()

info("Found plugins:\n")
for p in plugin_manager.getAllPlugins():
    info("\t%s\n" % p.name)

info("Activating plugins...\n")

# activate some plugins by default
plugin_manager.activatePluginByName("Raw")
plugin_manager.activatePluginByName("PacketParser")
plugin_manager.activatePluginByName("Shell")


info("Waiting for connections...\n")
reactor.listenTCP(listen_port, ClientProxyFactory((remote_host, remote_port)))
reactor.run()
