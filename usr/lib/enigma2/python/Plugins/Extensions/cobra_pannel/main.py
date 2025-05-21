from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import ePicLoad
from Screens.MessageBox import MessageBox
from Screens.Console import Console
import json
import os
import urllib.request
from urllib.parse import urlparse
import os.path

class CobraPanel(Screen):
    skin = """
        <screen name="CobraPanel" position="center,center" size="1000,620" title="Cobra Pannel">
            <widget name="info" position="30,30" size="940,40" font="Regular;32" />
            <widget name="menu" position="30,90" size="600,480" font="Regular;28" />
            <widget name="icon" position="660,180" size="300,300" alphatest="on" />
        </screen>
    """

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)

        self["info"] = Label("Seleziona un plugin da installare")
        self["menu"] = MenuList([])
        self["icon"] = Pixmap()

        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], {
            "ok": self.downloadSelected,
            "cancel": self.close,
            "up": self.up,
            "down": self.down,
        }, -1)

        self.picload = ePicLoad()
        self.pluginlist = []
        self.loadPlugins()

    def up(self):
        self["menu"].up()
        self.updateIcon()

    def down(self):
        self["menu"].down()
        self.updateIcon()

    def loadPlugins(self):
        try:
            url = "https://cobraliberosat.net/cobra_plugins/pluginlist.json"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                self.pluginlist = data
                names = [plugin["name"] for plugin in data]
                self["menu"].setList(names)
                self.updateIcon()
        except Exception as e:
            self["info"].setText(f"Errore caricamento lista: {str(e)}")

    def updateIcon(self):
        index = self["menu"].getSelectedIndex()
        if 0 <= index < len(self.pluginlist):
            image_url = self.pluginlist[index]["image"]
            local_path = "/tmp/plugin_icon.png"
            try:
                urllib.request.urlretrieve(image_url, local_path)
                self.picload.setPara((300, 300, 1, 1, False, 1, "#00000000"))
                if self.picload.startDecode(local_path, 0, 0, False) == 0:
                    ptr = self.picload.getData()
                    if ptr is not None:
                        self["icon"].instance.setPixmap(ptr)
            except Exception as e:
                print(f"Errore caricamento immagine: {e}")

    def downloadSelected(self):
        index = self["menu"].getSelectedIndex()
        if 0 <= index < len(self.pluginlist):
            plugin = self.pluginlist[index]
            name = plugin["name"]
            url = plugin["file"]
            self.session.openWithCallback(
                lambda x: self.startDownload(url) if x else None,
                MessageBox,
                f"Vuoi installare il plugin '{name}'?",
                MessageBox.TYPE_YESNO
            )

    def startDownload(self, url):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        local_path = f"/tmp/{filename}"
        try:
            urllib.request.urlretrieve(url, local_path)
            self.session.open(Console, title="Installazione Plugin", cmdlist=[f"opkg install --force-overwrite {local_path}"])
        except Exception as e:
            self.session.open(MessageBox, f"Errore nel download: {str(e)}", MessageBox.TYPE_ERROR)

