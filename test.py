import sys
import os
import re
import pyscreenshot as ImageGrab
from PIL import Image
import pytesseract
from fuzzywuzzy import fuzz
import win32api, win32gui, win32con
import sqlite3
import threading
import time

def click(x, y):
    hWnd = win32gui.FindWindow(None, "NoxPlayer")
    hWnd = win32gui.FindWindowEx(hWnd,0, "Qt5QWindowIcon","ScreenBoardClassWindow")
    hWnd = win32gui.FindWindowEx(hWnd,0, "Qt5QWindowIcon","QWidgetClassWindow")
    lParam = win32api.MAKELONG(55, 180)

    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)








