from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from enigma import ePicLoad
import os
import json
import urllib.request
import subprocess
from urllib.parse import urlparse

class CobraPanelScreen(Screen):  # <-- nome corretto per plugin.py
    skin = """
        <screen name="CobraPanel" position="center,center" size="900,700" title="Panel CBL">
            <widget name="title" position="10,10" size="600,40" font="Regular;28" />
            <widget name="list" position="10,60" size="600,500" font="Regular;26" itemHeight="40" />
            <widget name="icon" position="620,60" size="250,250" alphatest="on" />
            <widget name="status" position="620,320" size="40,40" alphatest="on" />
            <widget name="desc" position="620,380" size="250,180" font="Regular;22" />
            <widget name="logo" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo.png" position="690,190" size="150,150" alphatest="blend" />
            <widget name="logo2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo2.png" position="470,20" size="120,80" alphatest="blend" />
            <widget name="logo3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo3.png" position="690,530" size="150,150" alphatest="blend" />
            <widget name="footer" position="250,620" size="300,60" font="Regular;21" halign="center" valign="center" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["title"] = Label("Seleziona plugin da installare")
        self["list"] = MenuList([])
        self["icon"] = Pixmap()
        self["status"] = Pixmap()
        self["desc"] = Label("")
        self["logo"] = Pixmap()
        self["logo2"] = Pixmap()
        self["logo3"] = Pixmap()
        self["footer"] = Label("Cobra_Pannel - by CobraLiberosat")

        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], {
            "ok": self.confirmInstall,
            "cancel": self.close,
            "up": self.up,
            "down": self.down
        }, -1)

        self.plugins = []
        self.loadLogo()
        self.loadPlugins()

    def loadLogo(self):
        for logo_name in ["logo", "logo2", "logo3"]:
            logopath = f"/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/{logo_name}.png"
            try:
                if os.path.exists(logopath):
                    if hasattr(self[logo_name], 'instance') and self[logo_name].instance:
                        self[logo_name].instance.setPixmapFromFile(logopath)
                        self[logo_name].show()
                else:
                    self[logo_name].hide()
            except Exception as e:
                print(f"[COBRA LOGO] Errore caricamento {logo_name}: {e}")
                self[logo_name].hide()

    def loadPlugins(self):
        try:
            url = "https://cobraliberosat.net/cobra_plugins/pluginlist.json"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                self.plugins = data

            displaylist = []
            for plugin in self.plugins:
                pkg = os.path.basename(plugin["file"]).split("_")[0]
                installed = self.isInstalled(pkg)
                prefix = "● " if installed else "○ "
                displaylist.append(prefix + plugin["name"])

            self["list"].setList(displaylist)
            if self.plugins:
                self["list"].moveToIndex(0)
                self.updateInfo()
        except Exception as e:
            self["title"].setText("Errore nel caricamento dei plugin")
            self["desc"].setText(str(e))

    def isInstalled(self, pkgname):
        try:
            out = subprocess.getoutput(f"opkg list-installed | grep -i {pkgname}")
            return pkgname.lower() in out.lower()
        except:
            return False

    def updateInfo(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            self["desc"].setText("")
            self["icon"].hide()
            self["status"].hide()
            return

        plugin = self.plugins[index]
        self["desc"].setText(plugin.get("description", "Nessuna descrizione"))

        image_url = plugin.get("image", "")
        local_img = f"/tmp/plugin_img_{index}.png"
        try:
            if image_url.startswith("http"):
                urllib.request.urlretrieve(image_url, local_img)
                if hasattr(self["icon"], "instance") and self["icon"].instance:
                    self["icon"].instance.setPixmapFromFile(local_img)
                    self["icon"].show()
            else:
                if os.path.exists(image_url):
                    self["icon"].instance.setPixmapFromFile(image_url)
                    self["icon"].show()
                else:
                    self["icon"].hide()
        except Exception as e:
            print(f"Errore caricamento immagine plugin: {e}")
            self["icon"].hide()

        pkg_name = os.path.basename(plugin["file"]).split("_")[0]
        installed = self.isInstalled(pkg_name)
        icon_name = "green.png" if installed else "gray.png"
        icon_path = f"/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/icons/{icon_name}"

        try:
            if os.path.exists(icon_path):
                if hasattr(self["status"], "instance") and self["status"].instance:
                    self["status"].instance.setPixmapFromFile(icon_path)
                    self["status"].show()
            else:
                self["status"].hide()
        except Exception as e:
            print(f"Errore stato plugin: {e}")
            self["status"].hide()

    def up(self):
        self["list"].up()
        self.updateInfo()

    def down(self):
        self["list"].down()
        self.updateInfo()

    def confirmInstall(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        name = self.plugins[index]["name"]
        self.session.openWithCallback(
            self.startDownloadCallback,
            MessageBox,
            f"Vuoi installare il plugin '{name}'?",
            MessageBox.TYPE_YESNO
        )

    def startDownloadCallback(self, confirmed):
        if confirmed:
            index = self["list"].getSelectedIndex()
            url = self.plugins[index]["file"]
            self.startDownload(url)

    def startDownload(self, url):
        filename = os.path.basename(urlparse(url).path)
        local_path = f"/tmp/{filename}"
        try:
            urllib.request.urlretrieve(url, local_path)
            self.session.open(Console, title="Installazione Plugin", cmdlist=[f"opkg install --force-overwrite {local_path}"])
        except Exception as e:
            self.session.open(MessageBox, f"Errore nel download: {str(e)}", MessageBox.TYPE_ERROR)

