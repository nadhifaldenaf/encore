from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "static", "fonts")

def load_font(name, size):
    font_map = {
        "regular": "Poppins-Regular.ttf",
        "semibold": "Poppins-SemiBold.ttf",
        "bold": "Poppins-Bold.ttf",
        "black": "Poppins-Black.ttf",
    }
    return ImageFont.truetype(os.path.join(FONTS_DIR, font_map[name]), size)

def fetch_image(url):
    try:
        response = requests.get(url, timeout=15)
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        return None

def truncate_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    while len(text) > 0:
        text = text[:-1]
        if draw.textlength(text + "...", font=font) <= max_width:
            return text + "..."
    return "..."

def generate_story(data):
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), color="#0a0a0a")
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    font_black_52 = load_font("black", 52)
    font_bold_32 = load_font("bold", 32)
    font_bold_28 = load_font("bold", 28)
    font_bold_24 = load_font("bold", 24)
    font_semibold_30 = load_font("semibold", 30)
    font_regular_24 = load_font("regular", 24)
    font_regular_20 = load_font("regular", 20)

    # --- Colors ---
    white = "#FFFFFF"
    white_dim = "#888888"
    white_dimmer = "#444444"
    accent = "#FF6B6B"
    bg_card = "#141414"

    pad = 80

# --- Background foto artis ---
    if data.get("artist_cover"):
        cover = fetch_image(data["artist_cover"])
        if cover:
            cover = cover.convert("RGB")
            cover_h = 500
            # Crop ke rasio W:cover_h supaya tidak gepeng
            orig_w, orig_h = cover.size
            target_ratio = W / cover_h
            orig_ratio = orig_w / orig_h
            if orig_ratio > target_ratio:
                new_w = int(orig_h * target_ratio)
                left = (orig_w - new_w) // 2
                cover = cover.crop((left, 0, left + new_w, orig_h))
            else:
                new_h = int(orig_w / target_ratio)
                top = (orig_h - new_h) // 2
                cover = cover.crop((0, top, orig_w, top + new_h))
            cover_resized = cover.resize((W, cover_h), Image.LANCZOS)
            img.paste(cover_resized, (0, 0))
            overlay = Image.new("RGB", (W, cover_h), "#0a0a0a")
            mask = Image.new("L", (W, cover_h))
            mask_draw = ImageDraw.Draw(mask)
            for y_pos in range(cover_h):
                alpha = int(210 + (y_pos / cover_h) * 45)
                mask_draw.line([(0, y_pos), (W, y_pos)], fill=min(alpha, 255))
            img.paste(overlay, (0, 0), mask)
            dark_bottom = Image.new("RGB", (W, H - cover_h), "#0a0a0a")
            img.paste(dark_bottom, (0, cover_h))

    y = 110

    # --- Brand ---
    draw.text((pad, y), "encore.", font=font_black_52, fill=white)
    y += 80

    # --- User name + period ---
    user_label = f"{data['user_name']}'s Music Receipt"
    draw.text((pad, y), user_label, font=font_bold_32, fill=white)
    y += 50
    draw.text((pad, y), data["time_range_label"][data["time_range"]], font=font_regular_24, fill=white_dim)
    y += 60

    # --- Divider ---
    draw.line([(pad, y), (W - pad, y)], fill=white_dimmer, width=1)
    y += 48

    # --- Badges grid ---
    badges = [
        ("PERSONALITY", data["personality"]),
        ("LOYALTY", data["loyalty_badge"]),
        ("#1 ALL TIME", data["top_artist_alltime"]),
        ("CONSISTENCY", data["consistency"]),
    ]
    cell_w = (W - pad * 2) // 2
    cell_h = 120
    for i, (label, value) in enumerate(badges):
        col = i % 2
        row = i // 2
        x = pad + col * cell_w
        by = y + row * cell_h
        draw.rectangle([x + 2, by + 2, x + cell_w - 6, by + cell_h - 6], fill=bg_card)
        draw.text((x + 18, by + 16), label, font=font_regular_20, fill=white_dimmer)
        color = accent if label == "PERSONALITY" else white
        value_text = truncate_text(draw, value, font_bold_24, cell_w - 36)
        draw.text((x + 18, by + 46), value_text, font=font_bold_24, fill=color)
    y += cell_h * 2 + 48

    # --- Divider ---
    draw.line([(pad, y), (W - pad, y)], fill=white_dimmer, width=1)
    y += 48

    # --- Top Tracks ---
    if data.get("tracks"):
        draw.text((pad, y), "TOP TRACKS", font=font_regular_20, fill=white_dimmer)
        y += 44
        for i, track in enumerate(data["tracks"][:5]):
            num = f"{i+1:02d}"
            draw.text((pad, y + 4), num, font=font_regular_24, fill=white_dimmer)
            title = truncate_text(draw, track["title"], font_semibold_30, W - pad * 2 - 70)
            draw.text((pad + 60, y), title, font=font_semibold_30, fill=white)
            y += 40
            artist = truncate_text(draw, track["artist"], font_regular_24, W - pad * 2 - 70)
            draw.text((pad + 60, y), artist, font=font_regular_24, fill=white_dim)
            y += 50
        y += 24

    # --- Divider ---
    draw.line([(pad, y), (W - pad, y)], fill=white_dimmer, width=1)
    y += 48

    # --- Top Artists ---
    if data.get("artists"):
        draw.text((pad, y), "TOP ARTISTS", font=font_regular_20, fill=white_dimmer)
        y += 44
        for i, artist in enumerate(data["artists"][:5]):
            num = f"{i+1:02d}"
            draw.text((pad, y + 4), num, font=font_regular_24, fill=white_dimmer)
            name = truncate_text(draw, artist["name"], font_semibold_30, W - pad * 2 - 70)
            draw.text((pad + 60, y), name, font=font_semibold_30, fill=white)
            y += 60
        y += 24

    # --- Divider ---
    draw.line([(pad, y), (W - pad, y)], fill=white_dimmer, width=1)
    y += 48

    # --- QR Code ---
    try:
        import qrcode
        qr = qrcode.make("https://encore.up.railway.app")
        qr = qr.convert("RGB").resize((130, 130), Image.LANCZOS)
        img.paste(qr, (pad, y))
        draw.text((pad + 160, y + 10), "find your receipt at", font=font_regular_20, fill=white_dim)
        draw.text((pad + 160, y + 44), "encore.up.railway.app", font=font_bold_28, fill=white)
    except:
        draw.text((pad, y), "encore.up.railway.app", font=font_bold_28, fill=white)

    return img