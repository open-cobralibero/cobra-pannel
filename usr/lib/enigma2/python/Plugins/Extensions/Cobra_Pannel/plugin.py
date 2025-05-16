from Plugins.Plugin import PluginDescriptor
from .main import CobraPanel

def main(session, **kwargs):
    session.open(CobraPanel)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Cobra_Pannel",
            description="Pannello plugin Cobra Liberosat",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        )
    ]

