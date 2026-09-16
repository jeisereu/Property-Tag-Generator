import os
import re
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from property_rules import CATEGORY_RULES, clean_tech_specs


DICT_LOGO = "DICT-Logo.png"


def create_qr_image(property_number: str, size=(375, 374)):
    """Create a high-redundancy QR code with a small centered DICT logo."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(property_number)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_image = qr_image.resize(size, Image.Resampling.LANCZOS)

    if not os.path.exists(DICT_LOGO):
        return qr_image

    logo = Image.open(DICT_LOGO).convert("RGBA")
    logo_size = int(min(size) * 0.20)
    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Add a white buffer so the logo does not merge with QR modules.
    buffer_size = logo_size + 12
    background = Image.new("RGB", (buffer_size, buffer_size), "white")
    logo_x = (buffer_size - logo.width) // 2
    logo_y = (buffer_size - logo.height) // 2
    background.paste(logo, (logo_x, logo_y), logo)

    paste_x = (qr_image.width - buffer_size) // 2
    paste_y = (qr_image.height - buffer_size) // 2
    qr_image.paste(background, (paste_x, paste_y))
    return qr_image


def resolve_csv_file(csv_file: str = "properties.csv") -> str:
    """Use the main CSV when available, otherwise use the sample CSV."""
    if os.path.exists(csv_file):
        return csv_file

    fallback_csv = "properties_sample.csv"
    if os.path.exists(fallback_csv):
        print(f"[!] '{csv_file}' not found. Using '{fallback_csv}'.")
        return fallback_csv

    return csv_file


def get_accountable_person(row, default_person: str = "N. TABO") -> str:
    """Return the row's accountable person, or the configured default."""
    value = row.get("person_accountable", "")
    if pd.isna(value):
        return default_person

    person = str(value).strip()
    if person.lower() in ["", "nan", "none", "n/a", "na"]:
        return default_person

    return person


def parse_property_entry(raw_text: str):
    """
    Parses messy, multi-line, or comma-separated inventory entries into:
    (Description, Model/Brand, Serial No). Leaves missing fields blank ("").
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "", "", ""

    text = raw_text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    first_line = lines[0] if lines else ""

    # 1. Serial Number Extraction
    sn = ""
    sn_match = re.search(r'(?:SN|S/N|Serial\s*(?:No\.?)?)\s*[:\-]?\s*([^\n\r]+)', text, re.IGNORECASE)
    if sn_match:
        val = sn_match.group(1).strip().strip('"\'')
        if val.lower() not in ["n/a", "na", "none", "nan"]:
            sn = val

    # 2. Category / Description Extraction
    desc = ""
    for pat, cat_name in CATEGORY_RULES:
        if re.search(pat, text, re.IGNORECASE):
            if cat_name == "Power Supply" and re.search(r'\bups\b', text, re.IGNORECASE):
                desc = "UPS"
            elif cat_name == "Cabinet" and re.search(r'\bdisplay\s*cabinet\b', text, re.IGNORECASE):
                desc = "DISPLAY CABINET"
            elif cat_name == "Rack" and re.search(r'\bshoe\s*rack\b', text, re.IGNORECASE):
                desc = "SHOE RACK"
            else:
                desc = cat_name
            break

    comma_parts = [p.strip() for p in re.split(r'[,;]', first_line) if p.strip()]
    if not desc:
        desc = comma_parts[0] if comma_parts else first_line[:20]

    # 3. Model / Brand Extraction
    explicit_brand = None
    brand_match = re.search(r'Brand\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    if brand_match:
        val = brand_match.group(1).strip()
        if val.lower() not in ["n/a", "none", "nan"]:
            explicit_brand = val

    explicit_model = None
    model_match = re.search(r'Model(?:\s*No\.?)?\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    if model_match:
        val = model_match.group(1).strip()
        if val.lower() not in ["n/a", "none", "nan"]:
            explicit_model = val

    explicit_engine = None
    eng_match = re.search(r'Engine\s*Model(?:\s*No\.?)?\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    if eng_match:
        val = eng_match.group(1).strip()
        if val.lower() not in ["n/a", "none", "nan"]:
            explicit_engine = val

    # If explicit_model exists but no explicit_brand, only attach clean brand names (like TP-Link)
    if explicit_model and not explicit_brand and len(comma_parts) > 1:
        for p in comma_parts[1:]:
            p_clean = p.strip()
            # If the chunk contains category words (e.g. "Monitor", "Chair", "Switch"), skip it!
            if desc.lower() in p_clean.lower() or any(w in p_clean.lower() for w in ["monitor", "chair", "table", "cabinet", "rack", "switch", "unit"]):
                continue
            # Only treat as brand if it is concise (1-2 words like "TP-Link", "Asus", "Gamdias")
            if len(p_clean.split()) <= 2:
                explicit_brand = p_clean
                break

    model_brand = ""
    if explicit_brand and explicit_model:
        model_brand = f"{explicit_brand} {explicit_model}"
    elif explicit_brand:
        model_brand = explicit_brand
    elif explicit_model:
        model_brand = explicit_model
    else:
        candidate = ""

        # A. Multi-line items (e.g. Line 1: "Monitor", Line 2: "GAMDIAS Monitor Atlas QHD27FIC 27" 180Hz...")
        if len(lines) > 1:
            second_line = lines[1]
            if not re.search(r'^(?:SN|S/N|Serial|Date|Cost|Engine)', second_line, re.IGNORECASE):
                cleaned_l2 = clean_tech_specs(second_line, desc)
                if cleaned_l2:
                    candidate = cleaned_l2
                elif not second_line.startswith(('-', '•', '*')):
                    candidate = second_line

            # If there is an engine model (e.g. 1E45F), attach it to the candidate
            if explicit_engine and candidate:
                candidate = f"{candidate} {explicit_engine}"

        # B. Comma-separated items
        if not candidate and len(comma_parts) > 1:
            sub_parts = []
            for p in comma_parts:
                p_clean = p.strip()
                # Skip category words so they don't leak into the model/brand box
                if p_clean.lower() in [
                    desc.lower(), "bluetooth and wifi dongle", "wifi dongle", "dongle",
                    "radio", "portable radio", "center table", "desk console", 
                    "desk rf unit", "rf unit", "aircon", "air conditioner", "desktop", 
                    "chair", "table", "cabinet", "rack", "webcam", "switch", "ups"
                ]:
                    continue
                # Normalize variations like "WINDOWTYPE" -> "WINDOW TYPE"
                p_clean = re.sub(r'\bWINDOWTYPE\b', 'WINDOW TYPE', p_clean, flags=re.IGNORECASE)
                sub_parts.append(p_clean)

            # Join with space for seamless brand + variant (e.g. "MABE WINDOW TYPE")
            candidate = " ".join(sub_parts) if sub_parts else ""

        # C. Single-line compound items
        if not candidate:
            rem = first_line
            words_to_strip = [
                desc, "SHOE RACK", "MULTI PURPOSE RACK", "MULTI-PURPOSE RACK",
                "RECTANGULAR", "COMPUTER WEBCAM", "WEBCAM", "DISPLAY CABINET",
                "WOODEN DISPLAY CABINET", "CABINET", "CHAIR", "TABLE", "NETWORK SWITCH", "SWITCH",
                "FINGERPRINT TIME ATTENDANCE DEVICE", "TIME ATTENDANCE DEVICE", "BIOMETRIC DEVICE"
            ]
            for w in words_to_strip:
                rem = re.sub(rf'\b{re.escape(w)}\b', '', rem, flags=re.IGNORECASE)
            candidate = rem.strip(' /,-;:\'"')

        # Clean up candidate
        candidate = clean_tech_specs(candidate, desc)
        candidate = re.sub(
            r'\b(?:Portable\s+Generator\s+Set|Generator\s+Set|Generator|Portable\s+Radio|Radio|Center\s+Table|Desk\s+Console|Desk\s+RF\s+Unit|RF\s+Unit|Wooden\s+Chair|Monobloc\s+Chair|Monoblock\s+Chair|Computer\s+Table|Folding\s+Chair|Foldable\s+Chair|Gang\s+Chair|Office\s+Chair|Executive\s+Chair|Chair|Foldable\s+Table|Office\s+Table|Table|Vertical\s+Cabinet|Steel\s+Cabinet|Cabinet|Webcam|Camera|Rack|Fingerprint\s+Time\s+Attendance\s+Device|Time\s+Attendance\s+Device)\b',
            '',
            candidate,
            flags=re.IGNORECASE
        ).strip(' ,;:')

        # If candidate is solely an enclosed model code like (SMLH5-11006), unwrap the parentheses
        paren_code_match = re.fullmatch(r'\(([A-Za-z0-9\-]+)\)', candidate.strip())
        if paren_code_match:
            candidate = paren_code_match.group(1)

        if candidate.lower() not in ["n/a", "none", "nan", ""]:
            model_brand = candidate

    return desc.upper(), model_brand, sn


def format_acq_date_cost(raw_date, raw_cost) -> str:
    """Formats acquisition date and cost. Returns empty string if both are missing."""
    date_str = "" if pd.isna(raw_date) else str(raw_date).strip()
    if date_str.lower() in ["nan", "none", "n/a"]:
        date_str = ""

    cost_str = "" if pd.isna(raw_cost) else str(raw_cost).strip()
    if cost_str.lower() in ["nan", "none", "n/a"]:
        cost_str = ""
    elif cost_str:
        if not re.search(r'(?:Php|PHP|₱)', cost_str):
            try:
                num = float(re.sub(r'[^\d.]', '', cost_str))
                cost_str = f"Php {num:,.2f}"
            except (ValueError, TypeError):
                cost_str = f"Php {cost_str}"

    if date_str and cost_str:
        return f"{date_str} / {cost_str}"
    elif cost_str:
        return cost_str
    elif date_str:
        return date_str
    return ""


def draw_text_fitted(draw, text, x, y, max_width, base_font_path, base_size=30, min_size=8):
    """Render text with auto-shrink so long values stay inside their field."""
    if not text:
        return
    size = base_size
    font = None
    while size >= min_size:
        try:
            font = ImageFont.truetype(base_font_path, size) if base_font_path else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            break
        bbox = draw.textbbox((x, y), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width or size <= min_size:
            break
        size -= 2
    draw.text((x, y), text, fill="black", font=font)


def draw_fitted_pdf_text(c, text, x, y, max_width=470, font_name="Helvetica-Bold", base_size=25, min_size=8):
    """
    Renders text directly in the PDF canvas with dynamic auto-shrinking so text
    fills the white pill nicely (size 27) without overflowing long entries.
    """
    if not text:
        return
    size = base_size
    while size > min_size:
        w = c.stringWidth(text, font_name, size)
        if w <= max_width:
            break
        size -= 1

    c.setFont(font_name, size)
    c.drawString(x, y, text)


def create_searchable_pdf(cards_data, template_image, base_output_pdf="All_Property_Tags_Searchable", max_pages_per_pdf=250, output_pdf_dir="output_pdf"):
    """
    Creates searchable PDFs split into batches and ALWAYS puts them inside 'output_pdf_dir'.
    Uses font size 25 with auto-fit so text boxes import large and readable in Canva.
    """
    try:
        from reportlab.pdfgen import canvas
    except ImportError:
        print("\n[!] 'reportlab' is not installed. Run: pip install reportlab")
        return

    total_cards = len(cards_data)
    if total_cards == 0:
        return

    # 1. Ensure the dedicated PDF folder exists
    os.makedirs(output_pdf_dir, exist_ok=True)

    # 2. Calculate batches
    num_batches = (total_cards + max_pages_per_pdf - 1) // max_pages_per_pdf

    for batch_idx in range(num_batches):
        start_idx = batch_idx * max_pages_per_pdf
        end_idx = min(start_idx + max_pages_per_pdf, total_cards)
        batch_cards = cards_data[start_idx:end_idx]

        # Name the file
        if num_batches > 1:
            file_name = f"{base_output_pdf}_Part_{batch_idx + 1}.pdf"
        else:
            file_name = f"{base_output_pdf}_Part_1.pdf"
            
        pdf_path = os.path.join(output_pdf_dir, file_name)

        c = canvas.Canvas(pdf_path, pagesize=(1155, 450))

        for card in batch_cards:
            # Draw background tag template
            c.drawImage(template_image, 0, 0, width=1155, height=450)

            # Draw QR code if present
            if card["qr_path"] and os.path.exists(card["qr_path"]):
                c.drawImage(card["qr_path"], 735, 37, width=375, height=374)

            c.setFillColorRGB(0, 0, 0)

            # Y coordinates shifted slightly downward for size 27 font
            coords = [
                (card["prop_no"], 353),
                (card["desc"], 303),
                (card["model_brand"], 253),
                (card["sn"], 203),
                (card["acq"], 153),
                (card["accountable"], 102),
            ]

            for text, y_pdf in coords:
                draw_fitted_pdf_text(
                    c=c,
                    text=text,
                    x=185,
                    y=y_pdf,
                    max_width=470,
                    font_name="Helvetica-Bold",
                    base_size=27,
                    min_size=8
                )

            c.showPage()

        c.save()
        print(f"[+] Created: '{pdf_path}' (Contains items {start_idx + 1} to {end_idx})")

    print(f"\nAll PDF batches successfully saved in: '{output_pdf_dir}/'")

def create_property_tags(
    csv_file: str = "properties.csv",
    template_image: str = "DICT R5 Property Tag.png",
    output_dir: str = "output_property_tags",
    accountable_person: str = "N. TABO"
):
    os.makedirs(output_dir, exist_ok=True)
    temp_qr_dir = os.path.join(output_dir, "_temp_qr")
    os.makedirs(temp_qr_dir, exist_ok=True)

    df = pd.read_csv(resolve_csv_file(csv_file))

    TEXT_X = 185
    MAX_TEXT_WIDTH = 470  # (originally 460)
    Y_PROPERTY_NO   = 71   # (originally 76)
    Y_DESCRIPTION   = 121  # (originally 126)
    Y_MODEL_BRAND   = 171  # (originally 176)
    Y_SERIAL_NO     = 221  # (originally 226)
    Y_ACQ_DATE_COST = 271  # (originally 276)
    Y_ACCOUNTABLE   = 322  # (originally 327)

    QR_BOX_X = 735
    QR_BOX_Y = 39
    QR_TARGET_SIZE = (375, 374)

    font_path = None
    for fp in ["arialbd.ttf", "Arial_Bold.ttf", "LiberationSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "C:\\Windows\\Fonts\\arialbd.ttf"]:
        if os.path.exists(fp):
            font_path = fp
            break

    cards_for_pdf = []

    for idx, row in df.iterrows():
        raw_prop_no = row.get("property_number", "")
        prop_no = "" if pd.isna(raw_prop_no) else str(raw_prop_no).strip()
        if prop_no.lower() in ["nan", "none", "n/a"]:
            prop_no = ""

        raw_desc = str(row.get("description", "")).strip()
        if not prop_no and not raw_desc:
            continue

        desc, model_brand, sn = parse_property_entry(raw_desc)
        acq_date_cost = format_acq_date_cost(row.get("date"), row.get("cost"))
        row_accountable_person = get_accountable_person(row, accountable_person)

        # Individual PNG
        tag = Image.open(template_image).convert("RGB")
        draw = ImageDraw.Draw(tag)

        # Draw non-empty text fields
        draw_text_fitted(draw, prop_no, TEXT_X, Y_PROPERTY_NO, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, desc, TEXT_X, Y_DESCRIPTION, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, model_brand, TEXT_X, Y_MODEL_BRAND, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, sn, TEXT_X, Y_SERIAL_NO, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, acq_date_cost, TEXT_X, Y_ACQ_DATE_COST, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, row_accountable_person, TEXT_X, Y_ACCOUNTABLE, MAX_TEXT_WIDTH, font_path, 30)

        # Draw QR code
        qr_file_path = None
        if prop_no:
            qr_img = create_qr_image(prop_no, QR_TARGET_SIZE)
            tag.paste(qr_img, (QR_BOX_X, QR_BOX_Y))

            qr_file_path = os.path.join(temp_qr_dir, f"qr_{idx}.png")
            qr_img.save(qr_file_path)

        safe_name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', prop_no) if prop_no else f"tag_{idx+1}_unassigned"
        out_png = os.path.join(output_dir, f"{safe_name}.png")
        tag.save(out_png, quality=95)

        cards_for_pdf.append({
            "prop_no": prop_no,
            "desc": desc,
            "model_brand": model_brand,
            "sn": sn,
            "acq": acq_date_cost,
            "accountable": row_accountable_person,
            "qr_path": qr_file_path
        })

        print(f"Generated: {out_png} -> [Desc: {desc or '(blank)'} | Model: {model_brand or '(blank)'} | SN: {sn or '(blank)'}]")

    create_searchable_pdf(
        cards_for_pdf, 
        template_image, 
        base_output_pdf="All_Property_Tags_Searchable", 
        max_pages_per_pdf=425,
        output_pdf_dir="output_pdf"
    )


if __name__ == "__main__":
    create_property_tags()