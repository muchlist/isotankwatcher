from config import Config
import pyqrcode
import os


def generate_qr(id: str):
    """
    Fungsi ini digunakan saat dokumen naik ke lvl 3
    pastikan ada folder bernama qr didalam folder static
    """

    qr = pyqrcode.create(f'http://36.66.224.227/doc/{id}')
    current_dir = os.getcwd()
    # path = os.path.join(current_dir, "static","qr", f"{id}.png")
    path_folder = Config.CUSTOM_QR_PATH
    path = os.path.join(path_folder, f"{id}.png")
    # Linux || path = os.path.join("/home","muchlis", "isotankwatcher", "static", "qr")
    qr.png(path, scale=8)
