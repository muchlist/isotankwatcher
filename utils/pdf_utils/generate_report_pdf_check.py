import datetime

import os.path as ospath
from config import Config
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


def generate_pdf(pdf_name: str, data_check_list: list, start_date, end_date):

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

    tbl = Table(data, colWidths=[30*mm, 160*mm])
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
        [f'PENGECEKAN PERIODE [{start_date_string}] s/d [{end_date_string}]'],
    ]

    tblstyle = TableStyle([
        ('GRID', (0, 0), (0, 0), 0.25, colors.black),
        ('ALIGN', (0, 0), (0, 0), 'LEFT')
    ])

    tbl = Table(data, colWidths=[190*mm])
    tbl.setStyle(tblstyle)
    story.append(tbl)
    story.append(Spacer(0, 5))

    """
    -------------------------------------------------------------------------
    DATA PENGECEKAN
    """
    data = [["NO", "NOMER KONTAINER", "WAKTU",
             "POSISI", "STATUS", ]]

    for i in range(len(data_check_list)):

        # mendapatkan nama posisi pengecekan yang sesuai
        position_check = get_position_activity(
            data_check_list[i]["container"]["activity"], data_check_list[i]["position_step"])

        data.append([para(str(i+1)),
                     para(data_check_list[i]["container"]["container_number"]),
                     para(data_check_list[i]["checked_at"].strftime(
                         "%d %b %H:%M")),
                     para(position_check),
                     para(data_check_list[i]["status"]), ])

    tblstyle = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.lightblue]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 1), (-1, -1), "TOP"),
    ])

    tbl = Table(data, colWidths=[20*mm, 50*mm,
                                 30*mm, 50*mm, 40*mm])  # total 190
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
