import os
import math

import pandas as pd
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from generate_pc import format_acq_date_cost, parse_property_entry


INPUT_CSV = "properties.csv"
TEMPLATE_IMAGE = "DICT R5 Property Tag.png"
OUTPUT_PDF = "output_pdf/Property_Tags_A4_Searchable.pdf"
ACCOUNTABLE_PERSON = "N. TABO"

# Original template dimensions from generate_pc.py.
TEMPLATE_WIDTH = 1155
TEMPLATE_HEIGHT = 450

# Change only this value to change the number of columns.
PAGE_WIDTH, PAGE_HEIGHT = A4
PAGE_MARGIN = 10
# White space between cards for cutting; increase these values for wider borders.
COLUMN_GAP = 2
ROW_GAP = 2
COLUMNS = 3
CARD_HEIGHT_INCHES = 1.0

FONT_NAME = "Helvetica-Bold"
BASE_FONT_SIZE = 27
MIN_FONT_SIZE = 8
MAX_TEXT_WIDTH = 470


def draw_fitted_text(pdf, text, x, y, max_width, font_size, min_size=MIN_FONT_SIZE):
    """Draw one searchable text field, shrinking it when necessary."""
    if not text:
        return

    size = font_size
    while size > min_size and pdf.stringWidth(text, FONT_NAME, size) > max_width:
        size -= 1

    pdf.setFont(FONT_NAME, size)
    pdf.drawString(x, y, text)


def load_cards():
    """Read and normalize the same property data used by generate_pc.py."""
    cards = []
    data = pd.read_csv(INPUT_CSV)
    qr_directory = os.path.join("output_property_tags", "_temp_qr")
    os.makedirs(qr_directory, exist_ok=True)

    for row_index, (_, row) in enumerate(data.iterrows()):
        raw_property_number = row.get("property_number", "")
        property_number = "" if pd.isna(raw_property_number) else str(raw_property_number).strip()
        if property_number.lower() in ["nan", "none", "n/a"]:
            property_number = ""

        raw_description = str(row.get("description", "")).strip()
        if not property_number and not raw_description:
            continue

        description, model_brand, serial_number = parse_property_entry(raw_description)
        acquisition = format_acq_date_cost(row.get("date"), row.get("cost"))

        qr_path = None
        if property_number:
            qr_path = os.path.join(qr_directory, f"qr_{row_index}.png")
            if not os.path.exists(qr_path):
                qr = qrcode.QRCode(box_size=10, border=2)
                qr.add_data(property_number)
                qr.make(fit=True)
                qr.make_image(fill_color="black", back_color="white").save(qr_path)

        cards.append({
            "prop_no": property_number,
            "desc": description,
            "model_brand": model_brand,
            "sn": serial_number,
            "acq": acquisition,
            "accountable": ACCOUNTABLE_PERSON,
            "qr_path": qr_path,
        })

    return cards


def draw_card(pdf, card, x, y, width, height):
    """Draw a scaled card image and its searchable text layer."""
    scale_x = width / TEMPLATE_WIDTH
    scale_y = height / TEMPLATE_HEIGHT

    pdf.drawImage(TEMPLATE_IMAGE, x, y, width=width, height=height)

    if card["qr_path"]:
        pdf.drawImage(
            card["qr_path"],
            x + 735 * scale_x,
            y + 37 * scale_y,
            width=375 * scale_x,
            height=374 * scale_y,
        )

    pdf.setFillColorRGB(0, 0, 0)
    fields = [
        (card["prop_no"], 185, 353),
        (card["desc"], 185, 303),
        (card["model_brand"], 185, 253),
        (card["sn"], 185, 203),
        (card["acq"], 185, 153),
        (card["accountable"], 185, 102),
    ]

    for text, original_x, original_y in fields:
        draw_fitted_text(
            pdf,
            text,
            x + original_x * scale_x,
            y + original_y * scale_y,
            MAX_TEXT_WIDTH * scale_x,
            BASE_FONT_SIZE * scale_y,
        )


def create_a4_pdf(cards):
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    pdf = canvas.Canvas(OUTPUT_PDF, pagesize=A4)

    card_width = (PAGE_WIDTH - (2 * PAGE_MARGIN) - (COLUMNS - 1) * COLUMN_GAP) / COLUMNS
    card_height = CARD_HEIGHT_INCHES * 72
    rows = math.floor(
        (PAGE_HEIGHT - (2 * PAGE_MARGIN) + ROW_GAP) / (card_height + ROW_GAP)
    )
    cards_per_page = COLUMNS * rows

    for card_index, card in enumerate(cards):
        page_index = card_index % cards_per_page
        row = page_index // COLUMNS
        column = page_index % COLUMNS

        x = PAGE_MARGIN + column * (card_width + COLUMN_GAP)
        y = PAGE_HEIGHT - PAGE_MARGIN - card_height - row * (card_height + ROW_GAP)
        draw_card(pdf, card, x, y, card_width, card_height)

        if page_index == cards_per_page - 1 or card_index == len(cards) - 1:
            pdf.showPage()

    pdf.save()
    page_count = (len(cards) + cards_per_page - 1) // cards_per_page
    print(
        f"[+] Created: '{OUTPUT_PDF}' ({len(cards)} cards, "
        f"{COLUMNS} columns x {rows} rows, {page_count} A4 page(s))"
    )


if __name__ == "__main__":
    create_a4_pdf(load_cards())
