import pyqrcode
import os

def generate_qr(id : str):
    #Fungsi ini digunakan saat dokumen naik ke lvl 3
    #pastikan ada folder bernama qr didalam folder static
    #URL nya doc
    qr = pyqrcode.create(f'http://192.168.1.1/doc/{id}')
    path = os.path.join("static","qr", f"{id}.png")
    qr.png(path, scale=8)