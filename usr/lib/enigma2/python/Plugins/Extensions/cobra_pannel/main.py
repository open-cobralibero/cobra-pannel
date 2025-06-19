#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Cobra_Pannel by CobraLiberosat - main.py
"""

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

class CobraPanel(Screen):
    skin = """
        <screen name="CobraPanel" position="center,center" size="1000,660" title="Panel CBL">
            <widget name="title" position="10,10" size="600,40" font="Regular;28" />
            <widget name="list" position="10,60" size="600,480" font="Regular;26" itemHeight="40" scrollbarMode="showOnDemand"/>
            <widget name="icon" position="620,60" size="250,250" alphatest="on" />
            <widget name="status" position="620,320" size="40,40" alphatest="on" />
            <widget name="desc" position="620,380" size="360,60" font="Regular;22" />
            <widget name="statusLabel" position="620,450" size="360,30" font="Regular;22" foregroundColor="#FFFFFF" />
            <widget name="logo" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo.png" position="680,120" size="210,210" alphatest="blend" />
            <widget name="logo2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo2.png" position="470,20" size="120,80" alphatest="blend" />
            <widget name="logo3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo3.png" position="690,530" size="150,150" alphatest="blend" />
            <widget name="footer_fixed" position="10,580" size="950,30" font="Regular;26" halign="center" valign="center" foregroundColor="#00FF00" />
            <widget name="footer_status" position="10,620" size="950,30" font="Regular;22" halign="center" valign="center" foregroundColor="#FFFFFF" />
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
        self["statusLabel"] = Label("")
        self["logo"] = Pixmap()
        self["logo2"] = Pixmap()
        self["logo3"] = Pixmap()
        self["footer_fixed"] = Label("Cobra_Pannel - by CobraLiberosat")
        self["footer_status"] = Label("")

        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
            "ok": self.confirmInstall,
            "cancel": self.close,
            "up": self.up,
            "down": self.down,
            "red": self.confirmUninstall
        }, -1)

        self.plugins = []
        self.loadPlugins()

    def loadPlugins(self):
        url = "https://cobraliberosat.net/cobra_plugins/pluginlist.json"
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode('utf-8')
                plugins_json = json.loads(data)
                if isinstance(plugins_json, list):
                    self.plugins = plugins_json
                elif isinstance(plugins_json, dict) and "plugins" in plugins_json:
                    self.plugins = plugins_json["plugins"]
        except Exception:
            self.plugins = []

        if not self.plugins:
            self.plugins = [
                {"name": "Test Plugin A", "description": "Plugin demo A", "file": "", "image": ""},
                {"name": "Test Plugin B", "description": "Plugin demo B", "file": "", "image": ""}
            ]
            self["footer_status"].setText("Errore: impossibile caricare la lista plugin. Controlla connessione o server.")
        else:
            self["footer_status"].setText("")

        displaylist = []
        for plugin in self.plugins:
            pkg = os.path.basename(plugin["file"]).split("_")[0]
            installed = self.isInstalled(pkg)
            prefix = "● " if installed else "○ "
            displaylist.append(prefix + plugin["name"])

        self["list"].setList(displaylist)
        if len(self.plugins) > 0:
            self["list"].moveToIndex(0)
        self.updateInfo()

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
            self["footer_status"].setText("")
            self["statusLabel"].setText("")
            return

        plugin = self.plugins[index]
        desc = plugin.get("description", "Nessuna descrizione")
        self["desc"].setText(desc)

        image_url = plugin.get("image", "")
        local_img = f"/tmp/plugin_img_{index}.png"
        try:
            if self["icon"].instance:
                if image_url.startswith("http"):
                    urllib.request.urlretrieve(image_url, local_img)
                    self["icon"].instance.setPixmapFromFile(local_img)
                elif os.path.exists(image_url):
                    self["icon"].instance.setPixmapFromFile(image_url)
                self["icon"].show()
        except:
            self["icon"].hide()

        pkg = os.path.basename(plugin["file"]).split("_")[0]
        installed = self.isInstalled(pkg)
        icon_name = "green.png" if installed else "red.png"
        icon_path = f"/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/icons/{icon_name}"
        try:
            if self["status"].instance and os.path.exists(icon_path):
                self["status"].instance.setPixmapFromFile(icon_path)
                self["status"].show()
            else:
                self["status"].hide()
        except:
            self["status"].hide()

        if installed:
            self["footer_status"].setText("● Plugin installato - Premi il tasto ROSSO per disinstallare")
            self["statusLabel"].setText("● Plugin installato")
        else:
            self["footer_status"].setText("○ Plugin non installato - Premi OK per installare")
            self["statusLabel"].setText("○ Plugin non installato")

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
        plugin = self.plugins[index]
        self.session.openWithCallback(
            self.startDownloadCallback,
            MessageBox,
            f"Vuoi installare il plugin '{plugin['name']}'?",
            MessageBox.TYPE_YESNO
        )

    def startDownloadCallback(self, confirmed):
        if confirmed:
            index = self["list"].getSelectedIndex()
            plugin = self.plugins[index]
            self.startDownload(plugin["file"])

    def startDownload(self, url):
        filename = os.path.basename(urlparse(url).path)
        local_path = f"/tmp/{filename}"
        try:
            urllib.request.urlretrieve(url, local_path)
            self.session.open(Console, title="Installazione Plugin", cmdlist=[f"opkg install --force-overwrite {local_path}"])
        except Exception as e:
            self.session.open(MessageBox, f"Errore nel download: {str(e)}", MessageBox.TYPE_ERROR)

    def confirmUninstall(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        plugin = self.plugins[index]
        pkg = os.path.basename(plugin["file"]).split("_")[0]
        if self.isInstalled(pkg):
            self.session.openWithCallback(
                lambda confirmed: self.uninstall(pkg) if confirmed else None,
                MessageBox,
                f"Vuoi disinstallare il plugin '{plugin['name']}'?",
                MessageBox.TYPE_YESNO
            )
        else:
            self.session.open(MessageBox, "Plugin non è installato.", MessageBox.TYPE_INFO)

    def uninstall(self, pkg):
        self.session.open(Console, title="Disinstallazione Plugin", cmdlist=[f"opkg remove --force-depends {pkg}"])
        self.loadPlugins()
