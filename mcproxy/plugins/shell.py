# -*- coding: utf-8 -*-

from textwrap import TextWrapper, dedent
from cmd import Cmd

from mcproxy.plugin import Plugin, plugin_manager

import sys

"""
the shell for the proxy.
"""

wrap = 50

class Shell(Plugin):
    """
    Plugin to provide a shell.  The shell is accessable through the console.
    Plugin will publish a resource for other plugins to connect to the shell.
    """

    def OnActivate(self):
        self.shell = ProxyShell(stdout=sys.stdout)
        plugin_manager.register_resource("shell", self.shell)


class OutputSplitter(object):
    def __init__(self, *out):
        self.outputs = out

    def write(self, text):
        [ o.write(text) for o in self.outputs ]

    def add(self, output):
        self.outputs.append(output)

class ProxyShell(Cmd):
    def __init__(self, stdout=None):
        Cmd.__init__(self)
        self.stdout = stdout
        self.wrap = wrap

    def add_output(self, output):
        if isinstance(self.stdout, OutputSplitter):
            self.stdout.add(output)
        else:
            self.stdout = OutputSplitter(self.stdout, output)

    def default(self, line):
        """
        When a command is not understood, it goes here.
        """

        try:
            l = line.split()
            plugin, cmd = l[:2]
        except (ValueError, IndexError):
            self.syntax_error(line)
            return

        try:
            args = l[2:]
        except IndexError:
            pass
        else:
            args = []

        
        plugin = plugin_manager.getPluginByName(plugin)
        plugin = plugin.plugin_object
        try:
            f = getattr(plugin, "cmd_" + cmd)
        except AttributeError:
            self.stdout.write("*** Plugin \"%s\" has no command: %s\n" % (plugin.name, cmd))
        else:
            f(args)


    def syntax_error(self, line):
        self.stdout.write('*** Unknown syntax: %s\n'%line)

    def do_add(self, line):
        """
        Add a plugin to the proxy.
        Usage: add [plugin name]
        """
        pass

    def do_remove(self, line):
        """
        Remove a plugin from the proxy.
        Usage: remove [plugin]
        """
        pass

    def do_enable(self, line):
        """
        Enable a plugin.
        Usage: enable [plugin]
        
        Plugin must already be added.
        """
        pass

    def do_disable(self, line):
        """
        Disable a plugin.
        Usage: disable [plugin]

        Plugin must laready be added.
        """
        pass

    def do_set(self, line):
        """
        Set a plugin's variable.
        Usage: set [plugin] [variable] [value]
        """
        try:
            plugin, name, value = line.split()
        except:
            return

        plugin = plugin_manager.getPluginByName(plugin)
        if plugin == None:
            return

        plugin.plugin_object.set(name, value)
        self.stdout.write("ok.")

    def do_show(self, line):
        """
        Show a plugin's variable.
        Usage show [plugin] [variable]

        If the variable is ommited, then all the variable will be shown.
        """
        if line == "":
            self.stdout.write("Show what?")

        try:
            plugin, name = line.split()
        except:
            plugin = line

        plugin = plugin_manager.getPluginByName(plugin)
        if plugin == None:
            return

        plugin = plugin.plugin_object

        l = plugin.get_variables()
        if l == None:
            self.stdout.write("This plugin has no variables.")
        else:
            v = [ "%s %s" % (key, value) for key, value in l.items() ]
            self.print_topics("Variables", v, 40, self.wrap)

    def do_reload(self, line):
        """
        Reload configuration files and scripts.
        Usage: reload

        not implimented
        """

    def do_status(self, line):
        """
        List plugins and status.
        Usage: list
        """
        def make_status(plugin):
            if plugin.is_activated == True:
                return "%s on" % plugin.name
            elif plugin.is_activated == False:
                return "%s off" % plugin.name

        p = [ make_status(p) for p in plugin_manager.getAllPlugins() ]
        self.print_topics("Plugins", p, 40, self.wrap)

    def do_quit(self, line):
        """
        Quit (not implimented)
        Usage: quit
        """
        pass

    def emptyline(self):
        return ""

    def formatdoc(self, text):
        text = dedent(text)

        #remove initial newline
        if text[0] =="\n":
            text = text[1:]
        return text

    # overloaded to dedent leading tabs on doc strings
    def do_help(self, arg):
        """
        Get help
        Usage: help [topic]
        """
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc=getattr(self, 'do_' + arg).__doc__
                    if doc:
                        doc = self.formatdoc(doc)
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,self.wrap)
            self.print_topics(self.misc_header,  help.keys(),15,self.wrap)
            self.print_topics(self.undoc_header, cmds_undoc, 15,self.wrap)
