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


def _draw_currency(draw, right_x, y, amount, num_font, symbol_font, fill, symbol_y_offset=0):
    """Draws '৳<amount>' right-aligned so its right edge sits at right_x.

    PIL's ImageFont loads a single font file with no fallback — if that font
    lacks a glyph it silently draws a tofu box instead. NataSans/SpaceMono
    don't include the Bengali Taka sign (U+09F3), so it has to be drawn with
    a font that does (symbol_font) while the digits keep using the site's
    normal font (num_font). symbol_y_offset nudges the symbol vertically to
    optically align its baseline with the digits, since the two fonts have
    different metrics — tune this by eye once you see it rendered.
    """
    amount_text = str(amount)
    symbol = "৳"

    sym_bbox = draw.textbbox((0, 0), symbol, font=symbol_font)
    sym_w = sym_bbox[2] - sym_bbox[0]
    num_bbox = draw.textbbox((0, 0), amount_text, font=num_font)
    num_w = num_bbox[2] - num_bbox[0]

    x = right_x - (sym_w + num_w)
    draw.text((x, y + symbol_y_offset), symbol, font=symbol_font, fill=fill)
    draw.text((x + sym_w, y), amount_text, font=num_font, fill=fill)
    return sym_w + num_w


def build_receipt_image(registration):
    """Draws a PNG receipt for a Registration and returns it as a BytesIO buffer."""
    event = registration.event
    segments = registration.segment.all()
    total_fee = sum(seg.fee for seg in segments)

    W = 800
    MARGIN = 48
    BORDER = 4
    PAD = 36
    ROW_H = 52
    SEG_ROW_H = 38
    MIN_H = 900

    # --- Canvas height scales with content instead of being hardcoded ---
    # Everything here is a fixed pixel budget except the segment list, which
    # depends on len(segments). Without this, a registration with enough
    # segments would push the TOTAL/footer text past the fixed-height canvas,
    # overlapping the bottom border (or drawing off-canvas entirely).
    HEADER_BLOCK = 30 + 50 + 40 + 20            # eyebrow + heading + "registered to" + divider gap
    INFO_ROWS = ROW_H * 4                        # trxid / email / payment method / status
    SEGMENTS_LABEL = 16 + 34                     # gap + "SEGMENTS" heading
    SEGMENTS_FOOTER_GAP = 12 + 26                # divider gap + gap before TOTAL row
    TOTAL_ROW_H = 40                             # room for the TOTAL row itself
    FOOTER_BLOCK = 50                            # gap + footer line

    content_h = (
        HEADER_BLOCK + INFO_ROWS + SEGMENTS_LABEL
        + SEG_ROW_H * len(segments)
        + SEGMENTS_FOOTER_GAP + TOTAL_ROW_H + FOOTER_BLOCK
    )
    H = max(MIN_H, MARGIN * 2 + PAD * 2 + content_h)

    img = Image.new('RGB', (W, H), INK)
    draw = ImageDraw.Draw(img)

    f_label   = _font('SpaceMono-Regular.ttf', 15)
    f_value   = _font('SpaceMono-Regular.ttf', 17)
    f_heading = _font('NataSans-Black.ttf', 34)
    f_sub     = _font('SpaceMono-Regular.ttf', 15)
    f_seg     = _font('NataSans-Bold.ttf', 18)
    f_total_l = _font('NataSans-Black.ttf', 20)
    f_total_v = _font('NataSans-Black.ttf', 26)

    # Bengali-script fonts, used only for the ৳ glyph (see _draw_currency).
    # Sizes are tuned to visually match f_value / f_total_v — adjust if the
    # symbol looks too big/small or misaligned once rendered.
    f_currency_sm = _font('NotoSansBengali-Regular.ttf', 18)
    f_currency_lg = _font('NotoSansBengali-Bold.ttf', 28)

    x0, y0 = MARGIN, MARGIN
    x1, y1 = W - MARGIN, H - MARGIN

    draw.rectangle([x0, y0, x1, y1], outline=PAPER, width=BORDER)

    cx = x0 + PAD
    cy = y0 + PAD
    right_edge = x1 - PAD

    draw.text((cx, cy), "REGISTRATION CONFIRMED", font=f_sub, fill=ACCENT)
    cy += 30

    draw.text((cx, cy), event.name, font=f_heading, fill=PAPER)
    cy += 50

    draw.text((cx, cy), f"Registered to: {registration.name}", font=f_sub, fill=PAPER)
    cy += 40

    draw.line([(cx, cy), (right_edge, cy)], fill=PAPER, width=2)
    cy += 20

    def row(label, value):
        nonlocal cy
        draw.text((cx, cy), label.upper(), font=f_label, fill=PAPER)
        bbox = draw.textbbox((0, 0), value, font=f_value)
        vw = bbox[2] - bbox[0]
        draw.text((right_edge - vw, cy - 2), value, font=f_value, fill=PAPER)
        cy += ROW_H
        draw.line([(cx, cy - 14), (right_edge, cy - 14)], fill=(80, 78, 90), width=1)

    row("Transaction ID", registration.trxid)
    row("Email", registration.email)
    row("Payment Method", f"{registration.get_paymeth_display()} — {registration.paynum}")
    row("Status", registration.get_status_display())

    cy += 16
    draw.text((cx, cy), "SEGMENTS", font=f_label, fill=PAPER)
    cy += 34

    for seg in segments:
        draw.text((cx, cy), seg.name.upper(), font=f_seg, fill=PAPER)
        _draw_currency(draw, right_edge, cy + 2, seg.fee, f_value, f_currency_sm, PAPER, symbol_y_offset=1)
        cy += SEG_ROW_H

    cy += 12
    draw.line([(cx, cy), (right_edge, cy)], fill=PAPER, width=2)
    cy += 26

    draw.text((cx, cy), "TOTAL", font=f_total_l, fill=PAPER)
    _draw_currency(draw, right_edge, cy - 4, total_fee, f_total_v, f_currency_lg, ACCENT, symbol_y_offset=2)
    cy += TOTAL_ROW_H

    footer_y = cy + 20
    draw.text((cx, footer_y), f"GSCCC · {event.date}", font=f_sub, fill=(120, 118, 130))

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer