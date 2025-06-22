from Plugins.Plugin import PluginDescriptor
from . import main

def main_session(session, **kwargs):
    session.open(main.CobraPanel)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Cobra_Pannel",
            description="Pannello CobraLiberosat per installare plugin",
            where=PluginDescriptor.WHERE_PLUGINMENU,  # Menu Plugin (tasto verde)
            icon="plugin.png",
            fnc=main_session
        ),
        PluginDescriptor(
            name="Cobra_Pannel",
            description="Pannello CobraLiberosat per installare plugin",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,  # Menu principale (tasto menu)
            fnc=main_session
        )
    ]

