import datetime

import os.path as ospath
from config import Config
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


def generate_pdf(pdf_name: str, data_info_list: list, start_date, end_date, activity, dammaged):

    # A4 = (210*mm,297*mm)
    path = Config.CUSTOM_REPORT_PATH
    doc = SimpleDocTemplate(f'{path}{pdf_name}',
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
        ["", "CONTAINER DAMAGE REPORT"]
    ]

    # (SPAN, (begincol, beginrow), (endcol, endrow))
    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('SPAN', (0, 0), (0, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])

    tbl = Table(data, colWidths=[35*mm, 165*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 10))

    """
    -------------------------------------------------------------------------
    DATA STATUS PENGECEKAN HEADER
    """
    start_date_string = str(start_date.strftime("%d %B %Y")).upper()
    end_date_string = str(end_date.strftime("%d %B %Y")).upper()

    data = [
        ['Tanggal Awal', f':     {start_date_string}'],
        ['Tanggal Akhir', f':     {end_date_string}'],
        ['Aktifitas', f':     {activity}'],
    ]

    if dammaged:
        data.append(
            ['Kerusakan', ':     Tampilkan hanya yang rusak']
        )

    tblstyle = TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
    ])

    tbl = Table(data, colWidths=[40*mm, 160*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    DATA PENGECEKAN
    """
    data = [["NO", "KONTAINER", "TANGGAL",
             "TIPE", "KAPAL", "AKTIFITAS", "KERUSAKAN", "LOKASI"]]

    for i in range(len(data_info_list)):

        # mendapatkan posisi kerusakan
        _position_and_status_damagged = get_position_damaged(
            data_info_list[i]["checkpoint_status"], data_info_list[i]["activity"])
        position_damage = _position_and_status_damagged[0]
        status_damage = _position_and_status_damagged[1]
        type_combo = f'{data_info_list[i]["tipe"]} {str(data_info_list[i]["size"])}'
        vessel_combo = f'{data_info_list[i]["vessel"]} {data_info_list[i]["voyage"]}'
        time = data_info_list[i]["created_at"].strftime(
            "%d %b %H:%M")
        container_number = data_info_list[i]["container_number"]
        activity = " - ".join(data_info_list[i]["activity"].split("-"))

        print(position_damage)

        data.append([para(str(i+1)),
                     para(container_number),
                     para(time),
                     para(type_combo),
                     para(vessel_combo),
                     para(activity),
                     para(status_damage),
                     para(position_damage),
                     ])

    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.lightblue]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 1), (-1, -1), "TOP"),
    ])

    tbl = Table(data, colWidths=[13*mm, 35*mm, 25*mm, 17*mm,
                                 33*mm, 25*mm, 25*mm, 27*mm])  # total 190
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 10))

    # BUILD THE PDF
    doc.build(story)


def para(text: str) -> Paragraph:
    """
    Menginputkan text dan mengembalikan paragraph normal
    """
    normal_style = getSampleStyleSheet()["Normal"]
    return Paragraph(text, normal_style)


def get_position_activity(activity, step):
    position = ""
    if activity == "RECEIVING-MUAT":
        if step == "one":
            position = "GATE IN (R)"
        elif step == "two":
            position = "CY LIFT-OFF (R)"
        elif step == "three":
            position = "CY LIFT-ON (R)"
        elif step == "four":
            position = "MUAT"
        else:
            position = "RECEIVING-MUAT"

    if activity == "BONGKAR-DELIVERY":
        if step == "one":
            position = "BONGKAR"
        elif step == "two":
            position = "CY LIFT-OFF (D)"
        elif step == "three":
            position = "DELIVERY-LIFT-ON (D)"
        elif step == "four":
            position = "GATE OUT (D)"
        else:
            position = "BONGKAR-DELIVERY"

    return position


def get_position_damaged(checkpoint_status, activity) -> (str, str):
    nihil = "NIHIL"
    passed = "PASS"
    status_one = checkpoint_status["one"]
    status_two = checkpoint_status["two"]
    status_three = checkpoint_status["three"]
    status_four = checkpoint_status["four"]

    if not (status_one == "" or status_one == passed or nihil in status_one):
        return [get_position_activity(activity, "one"), get_status(status_one)]
    elif not (status_two == "" or status_two == passed or nihil in status_two):
        return [get_position_activity(activity, "two"), get_status(status_two)]
    elif not (status_three == "" or status_three == passed or nihil in status_three):
        return [get_position_activity(activity, "three"), get_status(status_three)]
    elif not (status_four == "" or status_four == passed or nihil in status_four):
        return [get_position_activity(activity, "four"), get_status(status_four)]
    else:
        return ["NIHIL", "NIHIL"]


def get_status(status):
    if status == "":
        return ""
    return status.split(" :")[0]
