import os
import re
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont

CATEGORY_RULES = [
    (r'\b(system\s*unit)\b', "System Unit"),
    (r'\b(gaming\s*monitor|monitor|display)\b', "Monitor"),
    (r'\b(laptop|notebook)\b', "Laptop"),
    (r'\b(printer|all-in-one)\b', "Printer"),
    (r'\b(power\s*supply|ups|uninterruptible\s*power)\b', "Power Supply"),
    (r'\b(generator|genset)\b', "Generator"),
    (r'\b(vsat\s*plate|vsat,\s*plate)\b', "VSAT Plate"),
    (r'\b(vsat)\b', "VSAT"),
    (r'\b(ups|uninterruptible\s*power)\b', "UPS"),
    (r'\b(air\s*condition(?:er)?|aircon|split\s*type|window\s*type)\b', "Air Conditioner"),
    (r'\b(electric\s*fan|stand\s*fan|wall\s*fan|desk\s*fan)\b', "Electric Fan"),
    (r'\b(television|smart\s*tv|tv)\b', "Television"),
    (r'\b(wireless\s*router|router|access\s*point)\b', "Wireless Router"),
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
]

def parse_property_entry(raw_text: str):
    """
    Parses complex, inconsistent, or single-phrase inventory entries into:
    (Description, Model/Brand, Serial No)
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "UNKNOWN", "N/A", "N/A"

    text = raw_text.strip()
    first_line = text.splitlines()[0].strip()

    # 1. Serial Number Extraction (defaults to N/A if absent)
    sn = "N/A"
    sn_match = re.search(r'(?:SN|S/N|Serial\s*(?:No\.?)?)\s*[:\-]?\s*([^\n\r]+)', text, re.IGNORECASE)
    if sn_match:
        val = sn_match.group(1).strip().strip('"\'')
        if val:
            sn = val

    # 2. Extract Category (Description)
    desc = ""
    for pat, cat_name in CATEGORY_RULES:
        if re.search(pat, text, re.IGNORECASE):
            # Differentiate between UPS and Power Supply
            if cat_name == "Power Supply" and re.search(r'\bups\b', text, re.IGNORECASE):
                desc = "UPS"
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
        explicit_brand = brand_match.group(1).strip()

    explicit_model = None
    model_match = re.search(r'Model\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    if model_match:
        explicit_model = model_match.group(1).strip()

    if explicit_brand and explicit_model:
        model_brand = f"{explicit_brand} {explicit_model}"
    elif explicit_brand:
        model_brand = explicit_brand
    elif explicit_model:
        model_brand = explicit_model
    else:
        # Check remaining tokens after removing the category name
        remaining_parts = []
        for part in comma_parts:
            # If the part is basically the category itself (e.g. "Power Supply" or "VSAT"), skip it
            if part.lower() in desc.lower() or desc.lower() in part.lower():
                continue
            remaining_parts.append(part)

        if remaining_parts:
            model_brand = " ".join(remaining_parts)
        elif len(comma_parts) > 1 and comma_parts[-1].lower() != desc.lower():
            model_brand = comma_parts[-1]
        else:
            model_brand = "N/A"

        # Check for trailing attributes (like Color: White for blinds)
        if model_brand == "N/A":
            color_match = re.search(r'Color\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
            if color_match:
                model_brand = color_match.group(1).strip()

    # Clean residual category prefixes
    model_brand = re.sub(r'^(?:Stand fan|Gaming Monitor|Window Type)\s*', '', model_brand, flags=re.IGNORECASE).strip(' "\'')
    if not model_brand:
        model_brand = "N/A"

    return desc.upper(), model_brand, sn


def draw_text_fitted(draw, text, x, y, max_width, base_font_path, base_size=22):
    """Renders text and dynamically shrinks font size if it exceeds the white pill width."""
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


def compile_tags_to_pdf(output_dir="output_property_tags", pdf_filename="All_Property_Tags.pdf"):
    """Combines all generated tag images into a single multi-page PDF."""
    image_files = sorted([
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if f.lower().endswith((".png", ".jpg"))
    ])
    
    if not image_files:
        print("No images found to compile into PDF.")
        return

    images = [Image.open(f).convert("RGB") for f in image_files]
    images[0].save(pdf_filename, save_all=True, append_images=images[1:])
    print(f"\n[+] Created multi-page PDF: '{pdf_filename}' ({len(images)} pages)")
    print("    Upload this PDF directly into Canva to get all tags ready at once!")


def create_property_tags(
    csv_file: str = "properties.csv",
    template_image: str = "DICT R5 Property Tag.png",
    output_dir: str = "output_property_tags",
    accountable_person: str = "N. TABO"
):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_file)

    # Box coordinates
    TEXT_X = 185
    MAX_TEXT_WIDTH = 460
    Y_PROPERTY_NO    = 76
    Y_DESCRIPTION    = 126
    Y_MODEL_BRAND    = 176
    Y_SERIAL_NO      = 226
    Y_ACCOUNTABLE    = 327

    QR_BOX_X = 735
    QR_BOX_Y = 39
    QR_TARGET_SIZE = (375, 374)

    # Font path detection
    font_path = None
    for fp in ["arialbd.ttf", "Arial_Bold.ttf", "LiberationSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "C:\\Windows\\Fonts\\arialbd.ttf"]:
        if os.path.exists(fp):
            font_path = fp
            break

    for idx, row in df.iterrows():
        # Handle missing / NaN / blank property numbers
        raw_prop_no = row.get("property_number", "")
        if pd.isna(raw_prop_no):
            prop_no = ""
        else:
            prop_no = str(raw_prop_no).strip()
            if prop_no.lower() in ["nan", "none", "n/a"]:
                prop_no = ""

        raw_desc = str(row.get("description", "")).strip()
        if not prop_no and not raw_desc:
            # Skip completely empty CSV rows
            continue

        desc, model_brand, sn = parse_property_entry(raw_desc)

        tag = Image.open(template_image).convert("RGB")
        draw = ImageDraw.Draw(tag)

        # 1. Draw text fields (Property No. remains blank if empty)
        if prop_no:
            draw_text_fitted(draw, prop_no, TEXT_X, Y_PROPERTY_NO, MAX_TEXT_WIDTH, font_path, 22)
            
        draw_text_fitted(draw, desc, TEXT_X, Y_DESCRIPTION, MAX_TEXT_WIDTH, font_path, 22)
        draw_text_fitted(draw, model_brand, TEXT_X, Y_MODEL_BRAND, MAX_TEXT_WIDTH, font_path, 22)
        draw_text_fitted(draw, sn, TEXT_X, Y_SERIAL_NO, MAX_TEXT_WIDTH, font_path, 22)
        draw_text_fitted(draw, accountable_person, TEXT_X, Y_ACCOUNTABLE, MAX_TEXT_WIDTH, font_path, 22)

        # 2. Only generate QR code if a Property Number exists
        if prop_no:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(prop_no)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            qr_img = qr_img.resize(QR_TARGET_SIZE, Image.Resampling.LANCZOS)
            tag.paste(qr_img, (QR_BOX_X, QR_BOX_Y))

        # 3. Save PNG with safe filename
        if prop_no:
            safe_name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', prop_no)
        else:
            safe_name = f"tag_{idx+1}_unassigned"

        out_path = os.path.join(output_dir, f"{safe_name}.png")
        tag.save(out_path, quality=95)
        print(f"Generated: {out_path} -> [{desc} | {model_brand} | {sn}] (QR: {'YES' if prop_no else 'BLANK'})")

    print(f"\nFinished generating tags.")
    compile_tags_to_pdf(output_dir=output_dir, pdf_filename="All_Property_Tags.pdf")


if __name__ == "__main__":
    create_property_tags()