import math
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from generate_a4_searchable_pdf import (
    ACCOUNTABLE_PERSON,
    CARD_HEIGHT_INCHES,
    COLUMNS,
    COLUMN_GAP,
    INPUT_CSV,
    PAGE_HEIGHT,
    PAGE_MARGIN,
    PAGE_WIDTH,
    ROW_GAP,
    draw_card,
    load_cards,
)

OUTPUT_DIRECTORY = "output_pdf"
OUTPUT_BASENAME = "Property_Tags_A4_Searchable_Page"


def create_individual_a4_pdfs(cards):
    """Create one searchable, one-page PDF document for each A4 card sheet."""
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    card_width = (PAGE_WIDTH - (2 * PAGE_MARGIN) - (COLUMNS - 1) * COLUMN_GAP) / COLUMNS
    card_height = CARD_HEIGHT_INCHES * 72
    rows = math.floor(
        (PAGE_HEIGHT - (2 * PAGE_MARGIN) + ROW_GAP) / (card_height + ROW_GAP)
    )
    cards_per_page = COLUMNS * rows
    page_count = math.ceil(len(cards) / cards_per_page) if cards else 0

    for page_index in range(page_count):
        start_index = page_index * cards_per_page
        page_cards = cards[start_index:start_index + cards_per_page]
        output_path = os.path.join(
            OUTPUT_DIRECTORY,
            f"{OUTPUT_BASENAME}_{page_index + 1}.pdf",
        )
        pdf = canvas.Canvas(output_path, pagesize=A4)

        for card_index, card in enumerate(page_cards):
            row = card_index // COLUMNS
            column = card_index % COLUMNS
            x = PAGE_MARGIN + column * (card_width + COLUMN_GAP)
            y = PAGE_HEIGHT - PAGE_MARGIN - card_height - row * (card_height + ROW_GAP)
            draw_card(pdf, card, x, y, card_width, card_height)

        pdf.showPage()
        pdf.save()
        print(
            f"[+] Created: '{output_path}' ({len(page_cards)} cards, "
            f"page {page_index + 1} of {page_count})"
        )

    print(
        f"\nCreated {page_count} individual A4 PDF document(s) in "
        f"'{OUTPUT_DIRECTORY}/' ({len(cards)} cards, {COLUMNS} columns x {rows} rows)."
    )


if __name__ == "__main__":
    create_individual_a4_pdfs(load_cards())
