"""Fictional two-floor hotel plans (36 m x 21 m, 0.03 m per px)."""
from PIL import Image, ImageDraw, ImageFont
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except OSError:
    F = S = ImageFont.load_default()


def base(title):
    im = Image.new("RGB", (1200, 700), "white"); d = ImageDraw.Draw(im)
    for x in range(0, 1201, 100): d.line([(x, 0), (x, 700)], fill=(238, 238, 238))
    for y in range(0, 701, 100): d.line([(0, y), (1200, y)], fill=(238, 238, 238))
    d.rectangle([0, 0, 1199, 699], outline="black", width=8)
    d.text((14, 660), title, font=S, fill="black")
    d.rectangle([540, 0, 660, 120], outline="black", width=4); d.text((556, 50), "STAIR", font=S, fill="black")
    return im, d


im, d = base("BASEMENT  (36 m x 21 m)")
for x in (400, 820): d.line([(x, 0), (x, 700)], fill="black", width=5)
d.line([(400, 500), (820, 500)], fill="black", width=5)
d.rectangle([395, 280, 405, 360], fill="white"); d.rectangle([815, 280, 825, 360], fill="white"); d.rectangle([570, 495, 650, 505], fill="white")
d.text((140, 320), "SPA", font=F, fill="black"); d.text((520, 300), "MEETING", font=F, fill="black")
d.text((960, 320), "GYM", font=F, fill="black"); d.text((540, 560), "SERVICE", font=F, fill="black")
d.rectangle([690, 650, 710, 670], fill=(220, 0, 0)); d.text((716, 650), "IDF", font=S, fill=(220, 0, 0))
im.save("basement.png")

im, d = base("GROUND FLOOR  (36 m x 21 m)")
d.line([(0, 470), (1200, 470)], fill="black", width=5)
for x in (300, 600, 900): d.line([(x, 470), (x, 700)], fill="black", width=3)
d.rectangle([280, 465, 340, 475], fill="white"); d.rectangle([860, 465, 920, 475], fill="white")
d.text((120, 260), "LOBBY", font=F, fill="black"); d.text((820, 260), "RESTAURANT", font=F, fill="black")
d.text((80, 580), "SHOP", font=S, fill="black"); d.text((380, 580), "OFFICE", font=S, fill="black")
d.text((690, 580), "ROOM", font=S, fill="black"); d.text((990, 580), "ROOM", font=S, fill="black")
im.save("ground.png")
