import re


# Category rules (Specific definitions before generic ones)
CATEGORY_RULES = [
    # Network & IT
    (r'\b(system\s*unit)\b', "System Unit"),
    (r'\b(network\s*switch|gigabit\s*switch|smart\s*switch|poe\s*switch|\bswitch\b)\b', "Network Switch"),
    (r'\b(gaming\s*monitor|monitor|lcd\s*display|led\s*display|computer\s*display)\b', "Monitor"),
    (r'\b(laptop|notebook)\b', "Laptop"),
    (r'\b(3D\s*printer)\b', "3D Printer"),
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
    # Radio & Communications
    (r'\b(desk\s*console)\b', "Desk Console"),
    (r'\b(desk\s*rf\s*unit|rf\s*unit)\b', "Desk RF Unit"),
    (r'\b(transceiver|hf\s*radio)\b', "Radio Transceiver"),
    (r'\b(portable\s*radio|two-way\s*radio|\bradio\b)\b', "Radio"),
    # Tables
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
    """Remove technical specifications while preserving useful model details."""
    cleaned = text.strip()

    if re.search(r'^\s*[-*•–—]?\s*\d*\s*(?:shelves|drawers?|doors?|glass|wooden|layer|tier)', cleaned, re.IGNORECASE):
        return ""
    if re.search(r'(?:L\s*\d+|\d+\s*L|\b\d+\s*[xX*]\s*\d+)', cleaned) and not re.search(r'[A-Za-z]{4,}', cleaned):
        return ""
    if re.search(r'^\s*(?:Heavy\s*duty\s*)?L\s*\d+\s*[xX*]\s*W\s*\d+', cleaned, re.IGNORECASE):
        return ""

    if desc:
        cleaned = re.sub(rf'\b{re.escape(desc)}\b', '', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r'\b(?:Desktop|Laptop)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:Fingerprint\s*Time\s*Attendance\s*Device|Time\s*Attendance\s*Device|Attendance\s*Device|Biometric\s*Device)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:Desk\s*Console|Desk\s*RF\s*Unit|RF\s*Unit)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:\w+\s+Tiered|\d+\s*Tiered|with\s+Glass\s+Top|Glass\s+Top)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')
    cleaned = re.sub(r'\b(?:4G\s*LTE|4G|LTE|PoC|Portable)\b', '', cleaned, flags=re.IGNORECASE).strip(' ,;:-')

    parens = re.findall(r'\([^)]*\)', cleaned)
    masked = cleaned
    for i, part in enumerate(parens):
        masked = masked.replace(part, f"__PAREN_{i}__")

    spec_triggers = [
        r'\b(?:High\s*Frequency|\(?HF\)?\s*radio|HF\s*radio)\b',
        r'\b\d+\s*Hz\b',
        r'\b(?:IPS|VA|TN|OLED)\b',
        r'\b\d{3,4}\s*[xX*]\s*\d{3,4}\b',
        r'\b(?:HDMI|DP\s*\d|DisplayPort|Audio\s*out|VGA)\b',
        r'\b(?:Flat|Curved|Wall\s*Bracket)\b',
        r'\b(?:Back\s*up|Backup)\b',
        r'(?<![-\w])\d+\s*(?:VA|kVA)\b',
        r'\b\d+\s*(?:watts?|W)\b',
        r'\b(?:with\s*Built-in|Built-in\s*AVR|AVR)\b',
        r'\b(?:\d+IEC|\d+\s*universal\s*socket|Outlet|socket)\b',
        r'\b(?:No\s*Software|GL-Fuse)\b',
        r'\b(?:\d+MP|\d+P\b|Full-HD|1080P|720P|4K|wide\s*angle|no\s*distortion|w/mic|heavy\s*duty)\b',
        r'\b(?:Nano\s+Wi-?Fi|Wi-?Fi\s+Bluetooth|Bluetooth\s*\d*(?:\.\d+)?)\b',
    ]

    match = re.search('|'.join(spec_triggers), masked, re.IGNORECASE)
    if match:
        masked = masked[:match.start()]

    for i, part in enumerate(parens):
        masked = masked.replace(f"__PAREN_{i}__", part)

    return re.sub(r'\s+', ' ', masked).strip(' ,;:-"\'')
