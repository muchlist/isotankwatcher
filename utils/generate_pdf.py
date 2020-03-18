from db import mongo
from bson.objectid import ObjectId
import datetime

import os.path as ospath
from config import Config
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


def generate_pdf(dc):
    # A4 = (210*mm,297*mm)
    path = Config.CUSTOM_PDF_PATH
    doc = SimpleDocTemplate(f'{path}{dc["_id"]}.pdf',
                            pagesize=A4,
                            rightMargin=72,
                            leftmargin=72,
                            topMargin=5,
                            bottomMargin=5)
    story = []

    """
    ------------------------------------------------------------------------
    DATA HEADER
    """
    img_path = Config.UPLOADED_IMAGES_DEST
    img = Image(img_path + "pelindo_logo.png", 68, 50, hAlign='CENTER')
    data = [
        [img, "Sistem Manajemen\nMutu, Keselamatan & Kesehatan Kerja, Keamanan, dan Lingkungan"],
        ["", "FORMULIR\nCONTAINER DAMAGE REPORT"]
    ]

    # (SPAN, (begincol, beginrow), (endcol, endrow))
    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('SPAN', (0, 0), (0, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])

    tbl = Table(data, colWidths=[30*mm, 160*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 10))

    """
    -------------------------------------------------------------------------
    DATA DETAIL KONTAINER
    """
    data = [
        ["KONTAINER", f': {dc["container_number"]}', "KAPAL",  f': {dc["vessel"]}'],
        ["UKURAN", f': {dc["size"]} FEET', "VOYAGE",  f': {dc["voyage"]}'],
        ["TIPE",  f': {dc["tipe"]}', "INT/DOM",  f': {dc["int_dom"]}'],
        ["STATUS",  f': {dc["full_or_empty"]}', "TANGGAL",  f': {dc["created_at"].strftime("%d %b %Y %H:%M:%S")}'],
        ["AKTIFITAS",  f': {dc["activity"]}', "", ""]
    ]

    tbl = Table(data, colWidths=[27*mm, 57*mm, 27*mm, 77*mm])
    story.append(tbl)
    story.append(Spacer(0, 10))

    """
    -------------------------------------------------------------------------
    DATA STATUS PENGECEKAN HEADER
    """

    data = [
        ["DETAIL PENGECEKAN"],
    ]

    tblstyle = TableStyle([
        ('GRID', (0, 0), (0, 0), 0.25, colors.black),
        ('ROWBACKGROUNDS', (0, 0), (0, 0), [colors.lightblue]),
        ('ALIGN', (0, 0), (0, 0), 'CENTER')
    ])

    tbl = Table(data, colWidths=[190*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    DATA STATUS PENGECEKAN
    """
    status = dc["status"]
    data = [["WAKTU", "LOKASI", "OLEH", "SAKSI", "CATATAN", "STATUS"], ]
    for st in status:
        data.append([para(st["checked_at"].strftime("%d %b %H:%M:%S")), para(st["check_position"]),
                     para(st["checked_by_name"]), para(st["witness"]), para(st["note"]), para(st["status"])])

    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.lightblue]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 1), (-1, -1), "TOP"),
    ])

    tbl = Table(data, colWidths=[30*mm, 20*mm, 25*mm, 25*mm, 70*mm, 20*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 10))

    """
    -------------------------------------------------------------------------
    FOTO HEADER
    """

    data = [
        ["FOTO KONTAINER"],
    ]

    tblstyle = TableStyle([
        ('GRID', (0, 0), (0, 0), 0.25, colors.black),
        ('ROWBACKGROUNDS', (0, 0), (0, 0), [colors.lightblue]),
        ('ALIGN', (0, 0), (0, 0), 'CENTER')
    ])

    tbl = Table(data, colWidths=[190*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    FOTO
    """
    path_img = Config.UPLOADED_IMAGES_DEST
    img_back = "[    ]"
    img_bottom = "[    ]"
    img_front = "[    ]"
    img_left = "[    ]"
    img_right = "[    ]"
    img_up = "[    ]"

    if dc["url_img_back"]:
        img_back = scale_image(path_img + dc["url_img_back"], 55*mm)
    if dc["url_img_bottom"]:
        img_bottom = scale_image(path_img + dc["url_img_bottom"], 55*mm)
    if dc["url_img_front"]:
        img_front = scale_image(path_img + dc["url_img_front"], 55*mm)
    if dc["url_img_left"]:
        img_left = scale_image(path_img + dc["url_img_left"], 55*mm)
    if dc["url_img_right"]:
        img_right = scale_image(path_img + dc["url_img_right"], 55*mm)
    if dc["url_img_up"]:
        img_up = scale_image(path_img + dc["url_img_up"], 55*mm)


    # img_back = scale_image(path_img + "2020B2/" +
    #                   "5e455b48496a4923018ce99b-M9PTQ.jpg", 55*mm)
    data = [
        [img_up, img_front, img_left],
        [img_bottom, img_back, img_right],
    ]
    tblstyle = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('ALIGN', (0, 0), (-1, -1), "CENTER"),
    ])
    tbl = Table(data, colWidths=[60*mm, 60*mm, 60*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    img_back = None
    img_bottom = None
    img_front = None
    img_left = None
    img_right = None
    img_up = None

    """
    -------------------------------------------------------------------------
    TANDA TANGAN
    """
    # cek apakah qr code ada
    img = Image(Config.UPLOADED_IMAGES_DEST + "finger_print.png", width=80, height=80)
    if ospath.isfile(Config.CUSTOM_QR_PATH + str(dc['_id']) + ".png"):
        img = Image(Config.CUSTOM_QR_PATH + str(dc['_id']) + ".png", width=80, height=80)

    data = [
        [f'{dc["agent"]}', "PELINDO III"],
        [img, img],
        [f'{dc["approval_agent_name"]}', f'{dc["approval_foreman_name"]}'],
    ]
    tblstyle = TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('ALIGN', (0, 0), (-1, -1), "CENTER"),
    ])
    tbl = Table(data, colWidths=[95*mm, 95*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)

    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    Disclaimer
    """
    data = [
        [para("""Catatan : Setiap kerusakan pada kontainer atau kargo yang ditemukan
     sebelum kontainer dibongkar dari kapal bukan tanggung jawab dari
     PT. PELABUHAN INDONESIA III""")],
    ]

    tbl = Table(data, colWidths=[190*mm])
    story.append(tbl)

    doc.build(story)


def para(text: str) -> Paragraph:
    """
    Menginputkan text dan mengembalikan paragraph normal
    """
    normal_style = getSampleStyleSheet()["Normal"]
    return Paragraph(text, normal_style)


def scale_image(image: str, desire_width: int) -> Image:
    """
    Menginputkan path image dan width dan mengembalikan scaled image
    """

    img = ImageReader(image)
    img_width, img_height = img.getSize()
    aspect = img_height / float(img_width)

    img = Image(image, width=desire_width, height=(
        desire_width * aspect), hAlign='CENTER')

    return img


if __name__ == "__main__":
    generate_pdf()
