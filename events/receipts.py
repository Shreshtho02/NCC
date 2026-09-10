import os
from io import BytesIO
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

INK = (10, 10, 12)
PAPER = (244, 237, 226)
ACCENT = (139, 92, 246)
FONT_DIR = os.path.join(settings.BASE_DIR, 'static', 'fonts')


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def build_receipt_image(registration):
    """Draws a PNG receipt for a Registration and returns it as a BytesIO buffer."""
    event = registration.event
    segments = registration.segment.all()
    total_fee = sum(seg.fee for seg in segments)

    W, H = 800, 1150
    MARGIN = 48
    BORDER = 4
    ROW_H = 52

    img = Image.new('RGB', (W, H), INK)
    draw = ImageDraw.Draw(img)

    f_label   = _font('SpaceMono-Regular.ttf', 15)
    f_value   = _font('SpaceMono-Regular.ttf', 17)
    f_heading = _font('NataSans-Black.ttf', 34)
    f_sub     = _font('SpaceMono-Regular.ttf', 15)
    f_seg     = _font('NataSans-Bold.ttf', 18)
    f_total_l = _font('NataSans-Black.ttf', 20)
    f_total_v = _font('NataSans-Black.ttf', 26)

    x0, y0 = MARGIN, MARGIN
    x1, y1 = W - MARGIN, H - MARGIN

    draw.rectangle([x0, y0, x1, y1], outline=PAPER, width=BORDER)

    pad = 36
    cx = x0 + pad
    cy = y0 + pad

    draw.text((cx, cy), "REGISTRATION CONFIRMED", font=f_sub, fill=ACCENT)
    cy += 30

    draw.text((cx, cy), event.name, font=f_heading, fill=PAPER)
    cy += 50

    draw.text((cx, cy), f"Registered to: {registration.name}", font=f_sub, fill=PAPER)
    cy += 40

    draw.line([(cx, cy), (x1 - pad, cy)], fill=PAPER, width=2)
    cy += 20

    def row(label, value):
        nonlocal cy
        draw.text((cx, cy), label.upper(), font=f_label, fill=PAPER)
        bbox = draw.textbbox((0, 0), value, font=f_value)
        vw = bbox[2] - bbox[0]
        draw.text((x1 - pad - vw, cy - 2), value, font=f_value, fill=PAPER)
        cy += ROW_H
        draw.line([(cx, cy - 14), (x1 - pad, cy - 14)], fill=(80, 78, 90), width=1)

    row("Transaction ID", registration.trxid)
    row("Email", registration.email)
    row("Payment Method", f"{registration.get_paymeth_display()} — {registration.paynum}")
    row("Status", registration.get_status_display())

    cy += 16
    draw.text((cx, cy), "SEGMENTS", font=f_label, fill=PAPER)
    cy += 34

    for seg in segments:
        draw.text((cx, cy), seg.name.upper(), font=f_seg, fill=PAPER)
        fee_text = f"৳{seg.fee}"
        bbox = draw.textbbox((0, 0), fee_text, font=f_value)
        vw = bbox[2] - bbox[0]
        draw.text((x1 - pad - vw, cy + 2), fee_text, font=f_value, fill=PAPER)
        cy += 38

    cy += 12
    draw.line([(cx, cy), (x1 - pad, cy)], fill=PAPER, width=2)
    cy += 26

    draw.text((cx, cy), "TOTAL", font=f_total_l, fill=PAPER)
    total_text = f"৳{total_fee}"
    bbox = draw.textbbox((0, 0), total_text, font=f_total_v)
    vw = bbox[2] - bbox[0]
    draw.text((x1 - pad - vw, cy - 4), total_text, font=f_total_v, fill=ACCENT)

    footer_y = y1 - pad - 20
    draw.text((cx, footer_y), f"GSCCC · {event.date}", font=f_sub, fill=(120, 118, 130))

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer