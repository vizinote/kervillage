# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""Genere assets/og-image.png (1200x630) pour Kervillage."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 1200, 630
PAPIER = (247, 243, 234)
ACCENT = (14, 79, 92)
ENCRE = (29, 42, 38)
DOUX = (76, 90, 84)
OR = (165, 119, 42)

img = Image.new("RGB", (W, H), PAPIER)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 14], fill=ACCENT)


def font(size, bold=False, serif=True):
    candidates = []
    if serif and bold:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
    elif serif:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
    elif bold:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    else:
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default()


marge = 90
d.text((marge, 170), "K E R V I L L A G E", font=font(40, bold=True, serif=False), fill=OR)
d.text((marge, 250), "Ton village", font=font(120, bold=True), fill=ACCENT)
d.text((marge, 385), "en breton", font=font(120, bold=True), fill=ACCENT)
d.text((marge, 545), "Nom breton, signification, décodeur de panneaux.",
       font=font(30, serif=False), fill=DOUX)
d.text((marge, H - 48), "kervillage.brozapi.com", font=font(26, serif=False), fill=OR)

img.save(os.path.join(ROOT, "assets", "og-image.png"))
print("og-image.png ecrit")
