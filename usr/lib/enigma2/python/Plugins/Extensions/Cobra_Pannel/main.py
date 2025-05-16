from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from enigma import ePicLoad
import urllib.request
import json
import os

class CobraPanel(Screen):
    skin = """
   <screen name="CobraPanel" position="center,center" size="900,560" title="Cobra Pannel">
        <widget name="info" position="20,20" size="860,40" font="Regular;24" />
        <widget name="menu" position="20,70" size="500,450" font="Regular;24" />
        <widget name="icon" position="540,150" size="320,240" alphatest="on" />
   </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.setTitle("Cobra Panel")

        self["info"] = Label("Benvenuto nel Cobra Panel - seleziona un plugin e premi OK")
        self["menu"] = MenuList([])
        self["icon"] = Pixmap()
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.updateIcon)

        self.plugins = []
        self.plugin_names = []

        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
            {
                "ok": self.installPlugin,
                "cancel": self.close,
                "up": self.keyUp,
                "down": self.keyDown
            }, -1)

        self.loadPlugins()

    def loadPlugins(self):
        try:
            if os.path.exists("/tmp/pluginlist.json"):
                with open("/tmp/pluginlist.json") as f:
                    data = json.load(f)
            else:
                url = "https://cobraliberosat.net/cobra_plugins/pluginlist.json"
                with urllib.request.urlopen(url) as r:
                    data = json.loads(r.read().decode())

            self.plugins = data
            self.plugin_names = [plugin["name"] for plugin in self.plugins]
            self["menu"].setList(self.plugin_names)
            self.updateImage()
        except Exception as e:
            self["menu"].setList(["Errore caricamento plugin: " + str(e)])

    def keyUp(self):
        self["menu"].up()
        self.updateImage()

    def keyDown(self):
        self["menu"].down()
        self.updateImage()

    def updateImage(self):
        index = self["menu"].getSelectedIndex()
        if 0 <= index < len(self.plugins):
            try:
                img_url = self.plugins[index].get("image", "")
                if not img_url.startswith("http"):
                    img_url = "https://cobraliberosat.net/cobra_plugins/" + img_url
                local_path = "/tmp/plugin_image.png"
                urllib.request.urlretrieve(img_url, local_path)
                self.picload.startDecode(local_path)
            except Exception:
                self["icon"].hide()
        else:
            self["icon"].hide()

    def updateIcon(self, picInfo=""):
        ptr = self.picload.getData()
        if ptr:
            self["icon"].instance.setPixmap(ptr)
            self["icon"].show()

    def installPlugin(self):
        index = self["menu"].getSelectedIndex()
        if 0 <= index < len(self.plugins):
            url = self.plugins[index].get("file", "")
            if not url:
                self["info"].setText("URL plugin non valido")
                return
            local_file = "/tmp/plugin.ipk"
            try:
                self["info"].setText("Scaricamento in corso...")
                urllib.request.urlretrieve(url, local_file)
                self["info"].setText("Installazione in corso...")
                ret = os.system(f"opkg install --force-overwrite {local_file}")
                if ret == 0:
                    self["info"].setText("Installazione completata. Riavvia la GUI.")
                else:
                    self["info"].setText("Errore durante l'installazione.")
            except Exception as e:
                self["info"].setText("Errore: " + str(e))
        else:
            self["info"].setText("Plugin non selezionato.")

