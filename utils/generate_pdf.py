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


def generate_pdf(data_info, data_check):

    # A4 = (210*mm,297*mm)
    path = Config.CUSTOM_PDF_PATH
    doc = SimpleDocTemplate(f'{path}{data_check["_id"]}.pdf',
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
    img_qr_code = Image(img_path + "pelindo_logo.png", 68, 50, hAlign='CENTER')
    data = [
        [img_qr_code, "Sistem Manajemen\nMutu, Keselamatan & Kesehatan Kerja, Keamanan, dan Lingkungan"],
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
    nopol_title = ""
    nopol = ""
    if data_check["nopol"] != "":
        nopol_title = "TRUCK"
        nopol = f': {data_check["nopol"].upper()}'

    data = [
        ["KONTAINER", f': {data_info["container_number"]}',
            "KAPAL",  f': {data_info["vessel"]}'],
        ["UKURAN", f': {data_info["size"]} FEET',
            "VOYAGE",  f': {data_info["voyage"]}'],
        ["TIPE",  f': {data_info["tipe"]}',
            "INT/DOM",  f': {data_info["int_dom"]}'],
        ["STATUS",  f': {data_info["full_or_empty"]}', nopol_title,
            nopol],
        ["AKTIFITAS",  f': {get_position_activity(data_check["container"]["activity"], data_check["position_step"])}',
         "TANGGAL", f': {data_info["created_at"].strftime("%d %b %Y %H:%M")}']
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
        ('ALIGN', (0, 0), (0, 0), 'LEFT')
    ])

    tbl = Table(data, colWidths=[190*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    DATA STATUS PENGECEKAN
    """
    data = [["WAKTU", "LOKASI", "CATATAN", "STATUS"], ]
    data.append([para(data_check["checked_at"].strftime("%d %b %H:%M")), para(data_check["position"]),
                 para(data_check["note"]), para(data_check["status"])])

    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.lightblue]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 1), (-1, -1), "TOP"),
    ])

    tbl = Table(data, colWidths=[30*mm, 30*mm, 95*mm, 35*mm])
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
        ('ALIGN', (0, 0), (0, 0), 'LEFT')
    ])

    tbl = Table(data, colWidths=[190*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    FOTO
    """

    image_data = data_check["image"]
    path_img = Config.UPLOADED_IMAGES_DEST
    img_back = "[    ]"
    img_bottom = "[    ]"
    img_front = "[    ]"
    img_left = "[    ]"
    img_right = "[    ]"
    img_up = "[    ]"

    if image_data["url_img_back"]:
        img_back = scale_image(path_img + image_data["url_img_back"], 55*mm)
    if image_data["url_img_bottom"]:
        img_bottom = scale_image(
            path_img + image_data["url_img_bottom"], 55*mm)
    if image_data["url_img_front"]:
        img_front = scale_image(path_img + image_data["url_img_front"], 55*mm)
    if image_data["url_img_left"]:
        img_left = scale_image(path_img + image_data["url_img_left"], 55*mm)
    if image_data["url_img_right"]:
        img_right = scale_image(path_img + image_data["url_img_right"], 55*mm)
    if image_data["url_img_up"]:
        img_up = scale_image(path_img + image_data["url_img_up"], 55*mm)

    # img_back = scale_image(path_img + "2020B2/" +
    #                   "5e455b48496a4923018ce99b-M9PTQ.jpg", 55*mm)
    data = [
        [img_front, img_left, img_up],
        [img_back, img_right, img_bottom],
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
    img_finger_print = Image(Config.UPLOADED_IMAGES_DEST +
                             "finger_print.png", width=90, height=90)

    # cek apakah qr code ada
    img_qr_code = img_finger_print
    if ospath.isfile(Config.CUSTOM_QR_PATH + str(data_check['_id']) + ".png"):
        img_qr_code = Image(Config.CUSTOM_QR_PATH +
                            str(data_check['_id']) + ".png", width=90, height=90)

    # cek apakah foto saksi ada
    img_witness = img_finger_print
    if data_check["image"]["url_img_witness"]:
        img_witness = scale_image(path_img + image_data["url_img_witness"], 90)

    # cek apakah foto tally ada
    # mengisi image tally dengan finger print
    img_tally = img_finger_print
    # membuat path untuk image profil
    folder = "profile"
    file_name = f'{data_check["approval"]["checked_by"]}.jpg'
    img_tally_path = ospath.join(
        path_img, folder, file_name)
    # cek apakah foto tally ada, jika ada isi img_tally dengan profil
    if ospath.isfile(img_tally_path):
        img_tally = scale_image(img_tally_path, 90)

    # cek apakah foto foreman ada
    # mengisi image foreman dengan finger print
    img_foreman = img_finger_print
    # membuat path untuk image profil
    folder = "profile"
    file_name = f'{data_check["approval"]["foreman"]}.jpg'
    img_foreman_path = ospath.join(
        path_img, folder, file_name)
    # cek apakah foto foreman ada, jika ada isi img_foreman dengan profil
    if ospath.isfile(img_foreman_path):
        img_foreman = scale_image(img_foreman_path, 90)

    # karena tiap step pengecekan siapa yang menjadi saksi berbeda2 profesi
    saksi = get_saksi(data_check["container"]
                      ["activity"], data_check["position_step"])

    data = [
        [saksi, "TALLY", "FOREMAN/MANAGER"],
        [img_witness, img_tally, img_foreman],
        [data_check["approval"]["witness"].upper(), data_check["approval"]["checked_by_name"],
            data_check["approval"]["foreman_name"]],
    ]
    tblstyle = TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('ALIGN', (0, 0), (-1, -1), "CENTER"),
    ])
    tbl = Table(data, colWidths=[63*mm, 63*mm, 63*mm])
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
     PT. PELABUHAN INDONESIA III"""), img_qr_code]
    ]

    tblstyle = TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.1, colors.grey),
        ('VALIGN', (0, 0), (0, 0), "TOP"),
        ('ALIGN', (0, 0), (-1, -1), "CENTER"),
    ])
    tbl = Table(data, colWidths=[126*mm, 63*mm])
    tbl.setStyle(tblstyle)
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

    img_qr_code = ImageReader(image)
    img_width, img_height = img_qr_code.getSize()
    aspect = img_height / float(img_width)

    img_qr_code = Image(image, width=desire_width, height=(
        desire_width * aspect), hAlign='CENTER')

    return img_qr_code


def get_saksi(activity, step):
    saksi = ""
    if activity == "RECEIVING-MUAT":
        if step == "one":
            saksi = "SOPIR TRUCK"
        elif step == "two":
            saksi = "OPERATOR"
        elif step == "three":
            saksi = "OPERATOR"
        elif step == "four":
            saksi = "PIHAK KAPAL"
        else:
            saksi = "SAKSI"

    if activity == "BONGKAR-DELIVERY":
        if step == "one":
            saksi = "PIHAK KAPAL"
        elif step == "two":
            saksi = "OPERATOR"
        elif step == "three":
            saksi = "SOPIR TRUCK"
        else:
            saksi = "SAKSI"

    return saksi


def get_position_activity(activity, step):
    saksi = ""
    if activity == "RECEIVING-MUAT":
        if step == "one":
            saksi = "GATE IN (R)"
        elif step == "two":
            saksi = "CY LIFT-OFF (R)"
        elif step == "three":
            saksi = "CY LIFT-ON (R)"
        elif step == "four":
            saksi = "MUAT"
        else:
            saksi = "RECEIVING-MUAT"

    if activity == "BONGKAR-DELIVERY":
        if step == "one":
            saksi = "BONGKAR"
        elif step == "two":
            saksi = "CY LIFT-OFF (D)"
        elif step == "three":
            saksi = "DELIVERY-LIFT-ON (D)"
        elif step == "four":
            saksi = "GATE OUT (D)"
        else:
            saksi = "BONGKAR-DELIVERY"

    return saksi
