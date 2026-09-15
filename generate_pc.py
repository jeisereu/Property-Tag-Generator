import os
import re
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont

# Category rules (Specific definitions before generic ones)
CATEGORY_RULES = [
    # Network & IT
    (r'\b(system\s*unit)\b', "System Unit"),
    (r'\b(network\s*switch|gigabit\s*switch|smart\s*switch|poe\s*switch|\bswitch\b)\b', "Network Switch"),
    (r'\b(gaming\s*monitor|monitor|lcd\s*display|led\s*display|computer\s*display)\b', "Monitor"),
    (r'\b(laptop|notebook)\b', "Laptop"),
    (r'\b(printer|all-in-one)\b', "Printer"),
    (r'\b(computer\s*webcam|webcam|web\s*camera)\b', "Webcam"),
    (r'\b(power\s*supply|ups|uninterruptible\s*power)\b', "Power Supply"),
    (r'\b(portable\s*generator\s*set|portable\s*genset)\b', "Portable Generator Set"),
    (r'\b(generator\s*set|generator|genset)\b', "Generator"),
    (r'\b(vsat\s*plate|vsat,\s*plate)\b', "VSAT Plate"),
    (r'\b(vsat)\b', "VSAT"),
    (r'\b(air\s*condition(?:er)?|aircon|split\s*type|window\s*type)\b', "Air Conditioner"),
    (r'\b(electric\s*fan|stand\s*fan|wall\s*fan|desk\s*fan)\b', "Electric Fan"),
    (r'\b(television|smart\s*tv|tv)\b', "Television"),
    (r'\b(wireless\s*access\s*point|access\s*point|\bwap\b)\b', "Wireless Access Point"),
    (r'\b(wireless\s*router)\b', "Wireless Router"),
    (r'\b(router)\b', "Router"),
    (r'\b(airfiber|ubiquiti\s*airfiber)\b', "Wireless Router"),
    (r'\b(paper\s*shredder|shredder)\b', "Paper Shredder"),
    (r'\b(fingerprint|biometric|attendance\s*device|time\s*attendance)\b', "Biometric Device"),
    (r'\b(speaker|soundbar)\b', "Speaker"),
    (r'\b(window\s*blinds|blinds)\b', "Window Blinds"),
    (r'\b(projector)\b', "Projector"),
    (r'\b(scanner)\b', "Scanner"),
    (r'\b(desktop)\b', "Desktop"),
    (r'\b(keyboard)\b', "Keyboard"),
    (r'\b(mouse)\b', "Mouse"),
    (r'\b(bluetooth\s*(?:and|&)\s*wi-?fi\s*dongle)\b', "Bluetooth and Wifi Dongle"),
    (r'\b(wi-?fi\s*dongle|wireless\s*dongle)\b', "Wifi Dongle"),
    (r'\b(bluetooth\s*dongle)\b', "Bluetooth Dongle"),
    (r'\b(dongle)\b', "Dongle"),

    # Chairs
    (r'\b(wooden\s*chair)\b', "Wooden Chair"),
    (r'\b(monobloc\s*chair|monoblock\s*chair|monobloc|monoblock)\b', "Monobloc Chair"),
    (r'\b(executive\s*chair)\b', "Executive Chair"),
    (r'\b(office\s*chair|clerical\s*chair|swivel\s*chair)\b', "Office Chair"),
    (r'\b(foldable\s*chair|folding\s*chair)\b', "Foldable Chair"),
    (r'\b(gang\s*chair)\b', "Gang Chair"),
    (r'\b(conference\s*chair)\b', "Conference Chair"),
    (r'\b(chair)\b', "Chair"),

    # Radio & Communications (Place ABOVE Tables)
    (r'\b(desk\s*console)\b', "Desk Console"),
    (r'\b(desk\s*rf\s*unit|rf\s*unit)\b', "Desk RF Unit"),
    (r'\b(transceiver|hf\s*radio)\b', "Radio Transceiver"),
    (r'\b(portable\s*radio|two-way\s*radio|\bradio\b)\b', "Radio"),

    # Tables (Specific types BEFORE generic Table)
    (r'\b(executive\s*table)\b', "Executive Table"),
    (r'\b(center\s*table)\b', "Center Table"),
    (r'\b(computer\s*table)\b', "Computer Table"),
    (r'\b(office\s*table|clerical\s*table)\b', "Office Table"),
    (r'\b(foldable\s*table|folding\s*table)\b', "Foldable Table"),
    (r'\b(conference\s*table)\b', "Conference Table"),
    (r'\b(dining\s*set|dining\s*table)\b', "Dining Set"),
    (r'\b(table|desk)\b', "Table"),

    # Storage, Cabinets & Racks
    (r'\b(display\s*cabinet|wooden\s*display\s*cabinet)\b', "Display Cabinet"),
    (r'\b(filing\s*cabinet|vertical\s*cabinet|lateral\s*cabinet|steel\s*cabinet|wooden\s*cabinet|cabinet)\b', "Cabinet"),
    (r'\b(shoe\s*rack)\b', "Shoe Rack"),
    (r'\b(multi\s*purpose\s*rack|storage\s*rack|server\s*rack|rack)\b', "Rack"),
]


def clean_tech_specs(text: str, desc: str = "") -> str:
    """
    Cleans long technical marketing buzzwords or spec descriptions from electronic gear.
    Protects text inside parentheses so model numbers like (AID1000-1000VA) are preserved.
    """
    cleaned = text.strip()

    if re.search(r'^\s*[-*•–—]?\s*\d*\s*(?:shelves|drawers?|doors?|glass|wooden|layer|tier)', cleaned, re.IGNORECASE):
        return ""
    # If line is purely physical measurements/dimensions (e.g. 100L x 50W x 75H or L180 x W74 x H74)
    if re.search(r'(?:L\s*\d+|\d+\s*L|\b\d+\s*[xX*]\s*\d+)', cleaned) and not re.search(r'[A-Za-z]{4,}', cleaned):
        return ""
    if re.search(r'^\s*(?:Heavy\s*duty\s*)?L\s*\d+\s*[xX*]\s*W\s*\d+', cleaned, re.IGNORECASE):
        return ""

    if desc:
        cleaned = re.sub(rf'\b{re.escape(desc)}\b', '', cleaned, flags=re.IGNORECASE)

    # Strip generic device descriptors that are not part of the brand/model name
    cleaned = re.sub(r'\b(?:Desktop|Laptop)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:Fingerprint\s*Time\s*Attendance\s*Device|Time\s*Attendance\s*Device|Attendance\s*Device|Biometric\s*Device)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:Desk\s*Console|Desk\s*RF\s*Unit|RF\s*Unit)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:\w+\s+Tiered|\d+\s*Tiered|with\s+Glass\s+Top|Glass\s+Top)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    # Strip communication buzzwords
    cleaned = re.sub(r'\b(?:4G\s*LTE|4G|LTE|PoC|Portable)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')

    # Mask text inside parentheses to prevent cutting off model codes like (AID1000-1000VA)
    parens = re.findall(r'\([^)]*\)', cleaned)
    masked = cleaned
    for i, p in enumerate(parens):
        masked = masked.replace(p, f"__PAREN_{i}__")

    spec_triggers = [
        r'\b(?:High\s*Frequency|\(?HF\)?\s*radio|HF\s*radio)\b', # Radio specs
        r'\b\d+\s*Hz\b',                                    # 180Hz, 144Hz
        r'\b(?:IPS|VA|TN|OLED)\b',                           # Panel types
        r'\b\d{3,4}\s*[xX*]\s*\d{3,4}\b',                  # 2560x1440, 1920x1080
        r'\b(?:HDMI|DP\s*\d|DisplayPort|Audio\s*out|VGA)\b', # Ports
        r'\b(?:Flat|Curved|Wall\s*Bracket)\b',              # Monitor features
        r'\b(?:Back\s*up|Backup)\b',                        # UPS Back up
        r'(?<![-\w])\d+\s*(?:VA|kVA)\b',                    # Matches 1200VA, but NOT hyphenated -1000VA
        r'\b\d+\s*(?:watts?|W)\b',                          # 650watts
        r'\b(?:with\s*Built-in|Built-in\s*AVR|AVR)\b',      # AVR
        r'\b(?:\d+IEC|\d+\s*universal\s*socket|Outlet|socket)\b', # Sockets
        r'\b(?:No\s*Software|GL-Fuse)\b',                   # Misc UPS notes
        r'\b(?:\d+MP|\d+P\b|Full-HD|1080P|720P|4K|wide\s*angle|no\s*distortion|w/mic|heavy\s*duty)\b',
        r'\b(?:Nano\s+Wi-?Fi|Wi-?Fi\s+Bluetooth|Bluetooth\s*\d*(?:\.\d+)?)\b', # Dongle / wireless specs
    ]

    pattern = '|'.join(spec_triggers)
    match = re.search(pattern, masked, re.IGNORECASE)
    if match:
        masked = masked[:match.start()]

    # Restore parentheses
    for i, p in enumerate(parens):
        masked = masked.replace(f"__PAREN_{i}__", p)

    cleaned = re.sub(r'\s+', ' ', masked).strip(' ,;:-"\'')
    return cleaned


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
        ).strip(' ,;:\'"')

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


def draw_text_fitted(draw, text, x, y, max_width, base_font_path, base_size=30):
    """Renders text in Pillow with auto-shrink."""
    if not text:
        return
    size = base_size
    font = None
    while size >= 12:
        try:
            font = ImageFont.truetype(base_font_path, size) if base_font_path else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            break
        bbox = draw.textbbox((x, y), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width or size <= 12:
            break
        size -= 2
    draw.text((x, y), text, fill="black", font=font)


def draw_fitted_pdf_text(c, text, x, y, max_width=470, font_name="Helvetica-Bold", base_size=25, min_size=12):
    """
    Renders text directly in the PDF canvas with dynamic auto-shrinking so text
    fills the white pill nicely (size 25) without overflowing long entries.
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

            # Y coordinates vertically re-aligned for size 25 font
            coords = [
                (card["prop_no"], 356),
                (card["desc"], 306),
                (card["model_brand"], 256),
                (card["sn"], 206),
                (card["acq"], 156),
                (card["accountable"], 105),
            ]

            for text, y_pdf in coords:
                draw_fitted_pdf_text(
                    c=c,
                    text=text,
                    x=185,
                    y=y_pdf,
                    max_width=470,
                    font_name="Helvetica-Bold",
                    base_size=25,
                    min_size=12
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

    df = pd.read_csv(csv_file)

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

        # Individual PNG
        tag = Image.open(template_image).convert("RGB")
        draw = ImageDraw.Draw(tag)

        # Draw non-empty text fields
        draw_text_fitted(draw, prop_no, TEXT_X, Y_PROPERTY_NO, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, desc, TEXT_X, Y_DESCRIPTION, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, model_brand, TEXT_X, Y_MODEL_BRAND, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, sn, TEXT_X, Y_SERIAL_NO, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, acq_date_cost, TEXT_X, Y_ACQ_DATE_COST, MAX_TEXT_WIDTH, font_path, 30)
        draw_text_fitted(draw, accountable_person, TEXT_X, Y_ACCOUNTABLE, MAX_TEXT_WIDTH, font_path, 30)

        # Draw QR code
        qr_file_path = None
        if prop_no:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(prop_no)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            qr_img = qr_img.resize(QR_TARGET_SIZE, Image.Resampling.LANCZOS)
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
            "accountable": accountable_person,
            "qr_path": qr_file_path
        })

        # print(f"Generated: {out_png} -> [Desc: {desc or '(blank)'} | Model: {model_brand or '(blank)'} | SN: {sn or '(blank)'}]")

    create_searchable_pdf(
        cards_for_pdf, 
        template_image, 
        base_output_pdf="All_Property_Tags_Searchable", 
        max_pages_per_pdf=425,
        output_pdf_dir="output_pdf"
    )


if __name__ == "__main__":
    create_property_tags()