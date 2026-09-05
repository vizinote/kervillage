# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""Genere assets/og-image.png (1200x630) pour Kervillage — palette Glaz & Ajonc."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 1200, 630
PAPIER = (251, 248, 240)   # FBF8F0
MER = (10, 62, 84)         # 0A3E54
ENCRE = (14, 42, 51)       # 0E2A33
DOUX = (76, 98, 103)       # 4C6267
AJONC = (200, 150, 46)     # C8962E
OR_TEXTE = (138, 100, 20)  # 8A6414

img = Image.new("RGB", (W, H), PAPIER)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 14], fill=MER)


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


def hermine(cx, cy, s, couleur):
    """Signe hermine : trois points + queue, centre en (cx, cy), echelle s."""
    for dx, dy, r in ((-3.4, -6, 1.5), (3.4, -6, 1.5), (0, -2, 1.7)):
        d.ellipse([cx + (dx - r) * s, cy + (dy - r) * s,
                   cx + (dx + r) * s, cy + (dy + r) * s], fill=couleur)
    # queue : triangle effile vers le bas, legerement courbe
    d.polygon([(cx - 1.4 * s, cy + 1 * s), (cx + 1.4 * s, cy + 1 * s),
               (cx + 0.7 * s, cy + 7.5 * s), (cx, cy + 8.6 * s),
               (cx - 0.7 * s, cy + 7.5 * s)], fill=couleur)


marge = 90

# badge hermine noir sur blanc, en haut a droite (rappel niveau 1)
bx, by, bs = W - marge - 96, 90, 96
d.rounded_rectangle([bx, by, bx + bs, by + bs + 18], radius=12, fill=(255, 255, 255),
                    outline=(10, 10, 10), width=2)
hermine(bx + bs / 2, by + (bs + 18) / 2 - 4, 6.0, (10, 10, 10))

d.text((marge, 150), "K E R V I L L A G E", font=font(40, bold=True, serif=False), fill=OR_TEXTE)
d.text((marge, 240), "Ton village", font=font(120, bold=True), fill=MER)
d.text((marge, 375), "en breton", font=font(120, bold=True), fill=MER)
d.rectangle([marge, 525, marge + 70, 529], fill=AJONC)
d.text((marge, 545), "Nom breton, signification, décodeur de panneaux.",
       font=font(30, serif=False), fill=DOUX)
d.text((marge, H - 48), "kervillage.brozapi.com", font=font(26, serif=False), fill=OR_TEXTE)

img.save(os.path.join(ROOT, "assets", "og-image.png"))
print("og-image.png ecrit")
