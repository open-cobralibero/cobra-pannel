#!/usr/bin/python
# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from enigma import eTimer
import os
import json
import subprocess
import urllib.request
from urllib.parse import urlparse
import re
from time import strftime

class CobraPanel(Screen):
    skin = """
        <screen name="CobraPanel" position="center,center" size="1180,710" title="Cobra Panel" backgroundColor="#101010">
            <widget name="background" position="0,0" size="1180,680" backgroundColor="#101010" zPosition="-100" />
            <widget name="logo_cobra" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo1.png" position="840,15" size="280,280" alphatest="blend" zPosition="10" />
            <widget name="logo4" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo4.png" position="490,260" size="580,300" alphatest="blend" zPosition="10" />
            <widget name="logo_small" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo_small.png" position="170,25" size="75,75" zPosition="5"/>
            <widget name="footer" position="240,25" size="900,40" font="Regular;24" foregroundColor="#daa520" halign="left" />
            <widget name="title" position="30,600" size="1120,30" font="Regular;22" halign="center" foregroundColor="#00FF00" />
            <widget name="list" position="30,100" size="450,520" font="Regular;24" itemHeight="36" scrollbarMode="showOnDemand" backgroundColor="#202020" foregroundColor="#FFFFFF"/>
            <widget name="icon" position="510,100" size="320,320" alphatest="on" backgroundColor="#303030"/>
            <widget name="desc" position="510,430" size="620,100" font="Regular;20" foregroundColor="#daa520" backgroundColor="#303030"/>
            <widget name="status" position="510,540" size="40,40" alphatest="on" zPosition="10"/>
            <widget name="statusLabel" position="560,540" size="570,40" font="Regular;22" foregroundColor="#FFFFFF"/>
            <widget name="button_ok" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/buttons/ok.png" position="160,665" size="150,40" alphatest="blend" zPosition="20"/>
            <widget name="legend_green" position="20,620" size="150,30" font="Regular;20" halign="center" foregroundColor="#FF0000" backgroundColor="#101010"/>
            <widget name="button_red" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/buttons/red.png" position="42,665" size="150,40" alphatest="blend" zPosition="20"/>
            <widget name="legend_red" position="140,620" size="120,30" font="Regular;20" halign="center" foregroundColor="#00FF00" backgroundColor="#101010"/>
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        # Widgets
        self["list"] = MenuList([])
        self["icon"] = Pixmap()
        self["desc"] = Label("")
        self["title"] = Label("Cobra_Pannel - by CobraLiberosat")
        self["status"] = Pixmap()
        self["statusLabel"] = Label("")
        self["logo_cobra"] = Pixmap()
        self["logo4"] = Pixmap()
        self["logo_small"] = Pixmap()
        self["button_ok"] = Pixmap()
        self["button_red"] = Pixmap()
        self["legend_green"] = Label("")
        self["legend_red"] = Label("")
        self["footer"] = Label("Cobra_Pannel - by CobraLiberosat")

        # Azioni
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "ok": self.installSelectedPlugin,
                "green": self.installSelectedPlugin,
                "cancel": self.close,
                "up": self.up,
                "down": self.down,
                "red": self.confirmUninstall,
            },
            -1,
        )

        # Dati
        self.plugins = []
        self.installed_packages = self.getInstalledPackages()
        self.error_loading = False

        # Timer aggiornamento info
        self.delayTimer = eTimer()
        self.delayTimer.callback.append(self.delayedUpdate)
        self.delayTimer.start(100, True)

        # Animazione logo
        self.logo_frames = [
            "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo1.png",
            "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo2.png",
            "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo3.png",
        ]
        self.logo_index = 0
        self.logo_timer = eTimer()
        self.logo_timer.callback.append(self.updateLogo)
        self.logo_timer.start(2000, False)  # 2 secondi per frame

        self.loadPlugins()

    def delayedUpdate(self):
        self.updateInfo()

    # ---------- Package Methods ----------
    def getInstalledPackages(self):
        installed = {}
        try:
            out = subprocess.getoutput("opkg list-installed")
            for line in out.splitlines():
                m = re.match(r"([^ ]+) - ([^ ]+)", line)
                if m:
                    installed[m.group(1).lower()] = m.group(2)
        except:
            pass
        return installed

    def parsePkgNameVersion(self, pkg_file):
        parts = pkg_file.split("_")
        pkg_name = parts[0].lower()
        pkg_version = ""
        if len(parts) > 1 and re.search(r"\d", parts[1]):
            pkg_version = parts[1]
        return pkg_name, pkg_version

    def isPluginInstalled(self, pkg_name, pkg_version):
        if pkg_name in self.installed_packages:
            if pkg_version:
                return self.installed_packages[pkg_name] == pkg_version
            return True
        return False

    # ---------- Load Plugins ----------
    def loadPlugins(self):
        url = "https://raw.githubusercontent.com/open-cobralibero/cobra_plugins/main/pluginlist.json"
        local_file = "/tmp/pluginlist.json"
        try:
            urllib.request.urlretrieve(url, local_file)
            with open(local_file, "r") as f:
                plugins_json = json.load(f)
                self.plugins = plugins_json if isinstance(plugins_json,list) else plugins_json.get("plugins",[])
            self.plugins.sort(key=lambda p: p.get("name","").lower())
            self.error_loading = False
        except:
            self.plugins = []
            self.error_loading = True
        self.fillList()
        self.updatePluginCount()

    def fillList(self):
        displaylist = []
        for plugin in self.plugins:
            pkg_file = os.path.basename(plugin["file"])
            pkg_name, pkg_version = self.parsePkgNameVersion(pkg_file)
            installed = self.isPluginInstalled(pkg_name, pkg_version)
            prefix = "● " if installed else "○ "
            displaylist.append((prefix + plugin["name"], plugin))
        self["list"].setList(displaylist)
        if self.plugins:
            self["list"].moveToIndex(0)

    # ---------- Update Info ----------
    def updateInfo(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        plugin = self.plugins[index]
        self["desc"].setText(plugin.get("description",""))

        # Immagine plugin
        image_url = plugin.get("image","")
        local_img = "/tmp/plugin_img_%d.png" % index
        try:
            if self["icon"].instance:
                if image_url.startswith("http"):
                    urllib.request.urlretrieve(image_url, local_img)
                    if os.path.exists(local_img):
                        self["icon"].instance.setPixmapFromFile(local_img)
                        self["icon"].show()
                    else:
                        self["icon"].hide()
                elif os.path.exists(image_url):
                    self["icon"].instance.setPixmapFromFile(image_url)
                    self["icon"].show()
                else:
                    self["icon"].hide()
        except:
            self["icon"].hide()

        pkg_file = os.path.basename(plugin["file"])
        pkg_name, pkg_version = self.parsePkgNameVersion(pkg_file)
        installed = self.isPluginInstalled(pkg_name, pkg_version)

        # Colori e cerchi
        if installed:
            icon_name = "red.png"
            self["legend_green"].setText("RIMUOVI")
            self["legend_red"].setText("")
            self["statusLabel"].setText("● Plugin installato")
        else:
            icon_name = "green.png"
            self["legend_red"].setText("INSTALLA")
            self["legend_green"].setText("")
            self["statusLabel"].setText("○ Plugin non installato")

        icon_path = "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/icons/%s" % icon_name
        if self["status"].instance and os.path.exists(icon_path):
            self["status"].instance.setPixmapFromFile(icon_path)
            self["status"].show()
        else:
            if self["status"].instance:
                self["status"].hide()

        self.updatePluginCount()

    def updatePluginCount(self):
        total = len(self.plugins)
        installed = sum(1 for p in self.plugins if self.isPluginInstalled(*self.parsePkgNameVersion(os.path.basename(p["file"]))))
        date_time = strftime("%d/%m/%Y %H:%M")
        self["footer"].setText(" 🐍 | {} | Plugin: {}/{}".format(date_time, installed, total))

    def clearInfo(self):
        self["desc"].setText("")
        self["statusLabel"].setText("")
        self["legend_green"].setText("")
        self["legend_red"].setText("")
        if self["icon"].instance:
            self["icon"].hide()
        if self["status"].instance:
            self["status"].hide()

    # ---------- Navigation ----------
    def up(self):
        self["list"].up()
        self.updateInfo()

    def down(self):
        self["list"].down()
        self.updateInfo()

    # ---------- Install / Uninstall ----------
    def installSelectedPlugin(self):
        index = self["list"].getSelectedIndex()
        if index<0 or index>=len(self.plugins):
            return
        plugin = self.plugins[index]
        self.session.openWithCallback(self.startDownloadCallback, MessageBox,
            "Vuoi installare il plugin '{}'?".format(plugin["name"]), MessageBox.TYPE_YESNO)

    def startDownloadCallback(self, confirmed):
        if not confirmed:
            return
        index = self["list"].getSelectedIndex()
        plugin = self.plugins[index]
        self.startDownload(plugin["file"])

    def startDownload(self, url):
        filename = os.path.basename(urlparse(url).path)
        local_path = "/tmp/%s"%filename
        try:
            urllib.request.urlretrieve(url, local_path)
            self.session.open(Console, title="Installazione Plugin", cmdlist=["opkg install --force-overwrite %s"%local_path])
            self.installed_packages = self.getInstalledPackages()
            self.loadPlugins()
        except Exception as e:
            self.session.open(MessageBox, "Errore nel download: %s"%str(e), MessageBox.TYPE_ERROR)

    def confirmUninstall(self):
        index = self["list"].getSelectedIndex()
        if index<0 or index>=len(self.plugins):
            return
        plugin = self.plugins[index]
        pkg_file = os.path.basename(plugin["file"])
        pkg_name, pkg_version = self.parsePkgNameVersion(pkg_file)
        if self.isPluginInstalled(pkg_name, pkg_version):
            self.session.openWithCallback(lambda confirmed: self.uninstall(pkg_name) if confirmed else None, MessageBox,
                                          "Vuoi disinstallare il plugin '{}'?".format(plugin["name"]), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, "Plugin non è installato.", MessageBox.TYPE_INFO)

    def uninstall(self, pkg_name):
        try:
            self.session.open(Console, title="Disinstallazione Plugin", cmdlist=["opkg remove --force-depends %s"%pkg_name])
            self.installed_packages = self.getInstalledPackages()
            self.loadPlugins()
        except Exception as e:
            self.session.open(MessageBox, "Errore nella disinstallazione: %s"%str(e), MessageBox.TYPE_ERROR)

    # ---------- Logo Animation ----------
    def updateLogo(self):
        self.logo_index = (self.logo_index + 1) % len(self.logo_frames)
        try:
            if self["logo_cobra"].instance:
                self["logo_cobra"].instance.setPixmapFromFile(self.logo_frames[self.logo_index])
        except:
            pass
        self.logo_timer.start(2000, False)  # 2 secondi/frame

