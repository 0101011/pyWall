# Author : globalpolicy
# Date   : March 2-4, 2017
# Script : pyWall
# Description : Change windows wallpaper
# Python : 3.5
# Blog   : c0dew0rth.blogspot.com

import requests
from bs4 import BeautifulSoup
import random
import shutil  # for copying raw image data(a file-like object) to an actual image file
import ctypes  # for calling Win32 API, specifically, SystemParametersInfo, to set wallpaper
import base64  # for turning original imagename into filesystem safe name
import tempfile  # for obtaining temp directory
import os  # for deleting file
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QTextEdit, QCheckBox, \
    QSystemTrayIcon  # for GUI
from PyQt5.QtGui import QFont, QIcon
import sys  # for sys.exit(app.exec_())
import threading  # for multithreading obviously
import time  # for timing utilities


class QTGui(QWidget):


    def __init__(self):
        super().__init__()
        self.showWindow()

    def changeEvent(self, QEvent):
        if QEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                print("minimized")
                self.minimizetotray()
        super().changeEvent(QEvent)

    def showWindow(self):
        self.setGeometry(300, 300, 300, 63)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("icon.png"))
        self.setWindowTitle("pyWall UI")

        global btn
        btn = QPushButton("Change", self)
        btn.resize(75, 23)
        btn.move(0, self.height() - btn.height())
        btn.setToolTip("Change the wallpaper right now.")
        btn.clicked.connect(newWallpaperInNewThread)
        global txtinterval
        txtinterval = QTextEdit("100", self)
        txtinterval.setToolTip("Time interval in seconds between wallpaper changes.")
        txtinterval.resize(70, 23)
        txtinterval.move(0, btn.y() - txtinterval.height())
        global chkbox
        chkbox = QCheckBox("Timer", self)
        chkbox.setToolTip("Use timer for auto wallpaper change.")
        chkbox.resize(49, 17)
        chkbox.move(0, txtinterval.y() - chkbox.height())
        chkbox.stateChanged.connect(checkBoxStateChanged)
        global label
        label = QLabel("", self)
        label.setFont(QFont("Times", 8, QFont.Bold))
        label.move(btn.width() + 5, 0)
        label.resize(self.width()-btn.width(),self.height())
        label.setWordWrap(True)
        self.show()

    def minimizetotray(self):
        self.hide()
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("icon.png"))
        self.tray.setToolTip("pyWall Tray")
        self.tray.show()
        self.tray.showMessage("pyWall", "pyWall will run in background.", msecs=500)
        self.tray.activated.connect(self.trayiconactivated)

    def trayiconactivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.tray.hide()
            self.show()


def checkBoxStateChanged(self):

    timerStatus = chkbox.checkState()  # chkbox.checkState() returns the "after-changed" status
    try:
        timerInterval = float(txtinterval.toPlainText())
    except ValueError:
        timerInterval = 300  # fail-safe value

    if timerStatus:  # True if checked
        global killThreadEvent
        killThreadEvent = threading.Event()
        threading.Thread(target=newWallpaperLoop, args=(timerInterval, killThreadEvent), daemon=True).start()
    else:
        killThreadEvent.set()  # setting this event will request the thread to stop


def main():
    app = QApplication(sys.argv)
    ui = QTGui()  # instantiate our GUI class wherein the form actually displays
    sys.exit(app.exec_())  # wait while GUI not closed


def newWallpaperInNewThread():
    threading.Thread(target=newWallpaper, daemon=True).start()


def newWallpaper():
    global savepath  # globalise for memory, for deleting the image next time this method executes
    try:
        os.remove(savepath)  # delete the last downloaded image, the wallpaper will not be affected
        print("Deleted ",savepath)
    except Exception as ex:
        print("Exception occurred while doing os.remove()\nException : ", ex)
    try:
        firstURL = "https://500px.com/popular"
        firstResponse = requests.get(firstURL)
        cookie = firstResponse.cookies["_hpx1"]
        content = firstResponse.content
        soup = BeautifulSoup(content, "lxml")
        found = soup.find("meta", attrs={"name": "csrf-token"})
        csrfToken = found["content"]

        randomPage = random.randint(1, 1000)
        apiURL = "https://api.500px.com/v1/photos"
        secondResponse = requests.get(apiURL, params={"rpp": 50, "feature": "popular", "image_size": 1080, "sort": "rating",
                                                      "exclude": "Nude", "formats": "jpeg", "page": randomPage},
                                      headers={"Cookie": "_hpx1=" + cookie, "X-CSRF-Token": csrfToken})

        # 500px API Reference:
        # https://github.com/500px/api-documentation/blob/master/endpoints/photo/GET_photos.md

        jsonResponse = secondResponse.json()
        randomIndex = random.randint(0, 49)
        randomImageLink = jsonResponse["photos"][randomIndex]["images"][0]["url"]
        randomImageName = jsonResponse["photos"][randomIndex]["name"]
        print(randomImageLink)
        print(randomImageName)

        label.setText(randomImageName)

        randomImageName = base64.urlsafe_b64encode(randomImageName.encode("UTF-8")).decode(
            "UTF-8")  # base64 encoding turns any imagename into a filesystem friendly name
        download = requests.get(randomImageLink, stream=True)  # stream=True is required to access download.raw data
    except Exception as ex:
        print("Something went wrong while downloading, no internet?\nException : ",ex)
        return

    try:
        savepath = tempfile.gettempdir() + "\\" + randomImageName + ".jpg"
        with open(savepath, "wb") as file:
            shutil.copyfileobj(download.raw, file)

        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, savepath,
                                                   0)  # ANSI version of the API doesn't seem to work here, thus the W
    except Exception as ex:
        print("Something went wrong while saving image.\nException : ", ex)
        return


def newWallpaperLoop(timerinterval, stop_event):
    while not stop_event.is_set():
        newWallpaperInNewThread()
        print("Spawning now!")
        time.sleep(timerinterval)
    print("stopped")


main()
