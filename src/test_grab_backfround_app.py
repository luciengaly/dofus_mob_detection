import cv2
import win32gui
import win32con
import win32api
import win32ui
from ctypes import windll
import numpy as np
from PIL import Image


def get_app_window(app_name):
    hwnd = win32gui.FindWindow(None, app_name)
    if hwnd:
        return hwnd
    else:
        print(f"Window with title '{app_name}' not found.")
        return None


def capture_video(hwnd):
    i = 0
    while True:
        # Obtenez les dimensions de la fenêtre
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        width, height = 1920, 1080

        # Prenez une capture d'écran de la fenêtre
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        save_bitmap = win32ui.CreateBitmap()
        # print(width, height)
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)

        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)
        if result == 1:
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)

            # Convertissez les bits en une image OpenCV
            img = np.frombuffer(bmpstr, dtype="uint8")
            img.shape = (bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4)

            # Retirez le canal alpha (transparence)
            img = img[:, :, :3]
            img = img[:, :, ::-1]

            # Affichez l'image avec OpenCV
            img = Image.fromarray(img)
            # left = 355
            # top = 38
            # right = left + 1210
            # bottom = top + 875
            left = 355 + 17
            top = 38
            right = left + 1210 - 17
            bottom = top + 875 - 7
            img = img.crop((left, top, right, bottom))
            img.save(f"test_grab/{i:03d}.png")
            # cv2.imshow("Application Frame", img)
            i += 1
            break

        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        # Arrêtez la boucle si la touche 'q' est pressée
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    # Remplacez 'YourApp' par le titre de la fenêtre de votre application
    app_name = "Deeplearner - Dofus 2.69.3.11"

    # Obtenez le handle de la fenêtre de l'application
    app_window_handle = get_app_window(app_name)

    if app_window_handle:
        # Appelez la fonction pour capturer le flux vidéo de l'application
        capture_video(app_window_handle)

        # Fermez toutes les fenêtres OpenCV à la fin
        cv2.destroyAllWindows()
