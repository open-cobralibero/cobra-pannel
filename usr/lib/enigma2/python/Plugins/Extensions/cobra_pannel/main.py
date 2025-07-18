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


class CobraPanel(Screen):
    skin = """
        <screen name="CobraPanel" position="center,center" size="1180,710" title="Cobra Panel" backgroundColor="#202020">
            <widget name="background" position="0,0" size="1180,680" backgroundColor="#202020" zPosition="-100" />
            <widget name="title" position="30,15" size="800,50" font="Regular;32" foregroundColor="#FFFFFF" />
            <widget name="list" position="30,80" size="450,520" font="Regular;24" itemHeight="36" scrollbarMode="showOnDemand" backgroundColor="#303030" foregroundColor="#FFFFFF" />
            <widget name="icon" position="510,80" size="320,320" alphatest="on" backgroundColor="#303030" />
            <widget name="desc" position="510,420" size="620,100" font="Regular;20" foregroundColor="#DDDDDD" backgroundColor="#303030" />
            <widget name="status" position="510,530" size="40,40" alphatest="on" zPosition="10" />
            <widget name="statusLabel" position="560,530" size="570,40" font="Regular;22" foregroundColor="#FFFFFF" />
            <widget name="logo" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo.png" position="840,15" size="280,280" alphatest="blend" zPosition="10" />
            <widget name="logo2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo2.png" position="490,260" size="580,300" alphatest="blend" zPosition="10" />
            <widget name="logo3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo3.png" position="800,620" size="280,280" alphatest="blend" zPosition="10" />
            <widget name="footer" position="30,600" size="1120,30" font="Regular;22" halign="center" foregroundColor="#AAAAAA" />
            <!-- Due label per legenda colorata -->
            <widget name="button_ok" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/buttons/ok.png" position="42,665" size="150,40" alphatest="blend" zPosition="20" />
            <widget name="legend_green" position="20,640" size="150,30" font="Regular;20" halign="center" foregroundColor="#00FF00" backgroundColor="#202020" />
            <widget name="button_red" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/buttons/red.png" position="160,665" size="150,40" alphatest="blend" zPosition="20" />
            <widget name="legend_red" position="130,640" size="150,30" font="Regular;20" halign="center" foregroundColor="#FF0000" backgroundColor="#202020" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["background"] = Pixmap()
        self["title"] = Label("Seleziona plugin da installare")
        self["list"] = MenuList([])
        self["icon"] = Pixmap()
        self["desc"] = Label("")
        self["status"] = Pixmap()
        self["statusLabel"] = Label("")
        self["logo"] = Pixmap()
        self["logo2"] = Pixmap()
        self["logo3"] = Pixmap()
        self["button_ok"] = Pixmap()
        self["button_red"] = Pixmap()
        self["legend_green"] = Label("")
        self["legend_red"] = Label("")
        self["footer"] = Label("Cobra_Pannel - by CobraLiberosat")

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

        self.plugins = []
        self.error_loading = False
        self.error_msg = ""

        self.delayTimer = eTimer()
        self.delayTimer.callback.append(self.delayedUpdate)
        self.delayTimer.start(100, True)

        self.loadBackground()
        self.loadLogo()
        self.loadPlugins()

    def delayedUpdate(self):
        self.updateInfo()

    def loadBackground(self):
        bg_path = "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/background.png"
        try:
            if os.path.exists(bg_path) and self["background"].instance:
                self["background"].instance.setPixmapFromFile(bg_path)
        except Exception as e:
            print("[CobraPanel] Errore loadBackground:", e)

    def loadLogo(self):
        logo_path = "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/logo.png"
        try:
            if os.path.exists(logo_path) and self["logo"].instance:
                self["logo"].instance.setPixmapFromFile(logo_path)
        except Exception as e:
            print("[CobraPanel] Errore loadLogo:", e)

    def loadPlugins(self):
        url = "https://cobraliberosat.net/cobra_plugins/pluginlist.json"
        local_file = "/tmp/pluginlist.json"
        try:
            print("[CobraPanel] Download JSON da:", url)
            urllib.request.urlretrieve(url, local_file)

            with open(local_file, "r") as f:
                data = f.read()
                plugins_json = json.loads(data)
                if isinstance(plugins_json, list):
                    self.plugins = plugins_json
                else:
                    self.plugins = plugins_json.get("plugins", [])

            self.plugins.sort(key=lambda p: p.get("name", "").lower())

            self.error_loading = False
            self.error_msg = ""
        except Exception as e:
            self.error_loading = True
            self.error_msg = str(e)
            self.plugins = []
            print("[CobraPanel] Errore caricamento plugin list:", e)

        self.fillList()

        def delayed_update():
            self.updateInfo()

        self._timer = eTimer()
        self._timer.callback.append(delayed_update)
        self._timer.start(50, True)

    def fillList(self):
        displaylist = []
        for plugin in self.plugins:
            try:
                pkg = os.path.basename(plugin["file"]).split("_")[0]
                installed = self.isInstalled(pkg)
                prefix = "● " if installed else "○ "
                displaylist.append(prefix + plugin["name"])
            except Exception as e:
                print("[CobraPanel] Errore elenco plugin:", e)

        self["list"].setList(displaylist)
        if self.plugins:
            self["list"].moveToIndex(0)

        if self.error_loading:
            self["footer"].setText("⚠ Errore: impossibile caricare la lista plugin.")
        else:
            self["footer"].setText("Cobra_Pannel - by CobraLiberosat")

    def isInstalled(self, pkgname):
        try:
            out = subprocess.getoutput("opkg list-installed | grep -i %s" % pkgname)
            return pkgname.lower() in out.lower()
        except Exception as e:
            print("[CobraPanel] Errore controllo installazione:", e)
            return False

    def updateInfo(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            self.clearInfo()
            return

        plugin = self.plugins[index]
        self["desc"].setText(plugin.get("description", "Nessuna descrizione"))

        image_url = plugin.get("image", "")
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
        except Exception as e:
            print("[CobraPanel] Errore caricamento immagine:", e)
            self["icon"].hide()

        pkg = os.path.basename(plugin["file"]).split("_")[0]
        installed = self.isInstalled(pkg)

        icon_name = "green.png" if installed else "red.png"
        icon_path = "/usr/lib/enigma2/python/Plugins/Extensions/cobra_pannel/icons/%s" % icon_name

        if self["status"].instance and os.path.exists(icon_path):
            self["status"].instance.setPixmapFromFile(icon_path)
            self["status"].show()
        else:
            if self["status"].instance:
                self["status"].hide()

        if installed:
            self["statusLabel"].setText("● Plugin installato")
            self["legend_green"].setText("")
            self["legend_red"].setText("ROSSO")
        else:
            self["statusLabel"].setText("○ Plugin non installato")
            self["legend_red"].setText("")
            self["legend_green"].setText("VERDE")

    def clearInfo(self):
        self["desc"].setText("")
        self["statusLabel"].setText("")
        if self["status"].instance:
            self["status"].hide()
        self["legend_green"].setText("")
        self["legend_red"].setText("")
        if self["icon"].instance:
            self["icon"].hide()

    def up(self):
        self["list"].up()
        self.updateInfo()

    def down(self):
        self["list"].down()
        self.updateInfo()

    def installSelectedPlugin(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        plugin = self.plugins[index]
        self.session.openWithCallback(
            self.startDownloadCallback,
            MessageBox,
            "Vuoi installare il plugin '{}'?".format(plugin["name"]),
            MessageBox.TYPE_YESNO,
        )

    def startDownloadCallback(self, confirmed):
        if not confirmed:
            return
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        plugin = self.plugins[index]
        self.startDownload(plugin["file"])

    def startDownload(self, url):
        filename = os.path.basename(urlparse(url).path)
        local_path = "/tmp/%s" % filename
        try:
            urllib.request.urlretrieve(url, local_path)
            self.session.open(
                Console,
                title="Installazione Plugin",
                cmdlist=["opkg install --force-overwrite %s" % local_path],
            )
        except Exception as e:
            print("[CobraPanel] Errore download/installazione:", e)
            self.session.open(
                MessageBox, "Errore nel download: %s" % str(e), MessageBox.TYPE_ERROR
            )

    def confirmUninstall(self):
        index = self["list"].getSelectedIndex()
        if index < 0 or index >= len(self.plugins):
            return
        pkg = os.path.basename(self.plugins[index]["file"]).split("_")[0]
        if self.isInstalled(pkg):
            plugin_name = self.plugins[index]["name"]
            self.session.openWithCallback(
                lambda confirmed: self.uninstall(pkg) if confirmed else None,
                MessageBox,
                "Vuoi disinstallare il plugin '{}'?".format(plugin_name),
                MessageBox.TYPE_YESNO,
            )
        else:
            self.session.open(MessageBox, "Plugin non è installato.", MessageBox.TYPE_INFO)

    def uninstall(self, pkg):
        self.session.open(
            Console, title="Disinstallazione Plugin", cmdlist=["opkg remove --force-depends %s" % pkg]
        )
        self.loadPlugins()

