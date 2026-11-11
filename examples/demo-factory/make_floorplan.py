"""Generate the fictional demo floor plan (96 m x 54 m, 0.06 m per px)."""
from PIL import Image, ImageDraw, ImageFont
im = Image.new("RGB", (1700, 1000), "white"); d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34); s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except OSError:
    f = s = ImageFont.load_default()
G = (200, 200, 200)
for x in range(50, 1651, 100): d.line([(x, 50), (x, 950)], fill=(235, 235, 235))
for y in range(50, 951, 100): d.line([(50, y), (1650, y)], fill=(235, 235, 235))
for y in range(150, 900, 120): d.rectangle([110, y, 790, y + 40], outline=G, width=2)   # racks
for x in (950, 1150, 1350): d.rectangle([x, 120, x + 120, 580], outline=G, width=2)      # machines
d.rectangle([50, 50, 1650, 950], outline="black", width=6)
d.line([(850, 50), (850, 950)], fill="black", width=5)
d.line([(850, 650), (1650, 650)], fill="black", width=5)
for x in (1100, 1350): d.line([(x, 650), (x, 950)], fill="black", width=3)               # office rooms
d.rectangle([845, 300, 855, 380], fill="white"); d.rectangle([1500, 645, 1560, 655], fill="white")  # doors
d.rectangle([860, 890, 880, 910], fill=(220, 0, 0))
d.text((864, 912), "IDF", font=s, fill=(220, 0, 0))
d.text((330, 470), "WAREHOUSE", font=f, fill="black"); d.text((1120, 600), "PRODUCTION", font=f, fill="black")
d.text((1180, 860), "OFFICE", font=f, fill="black")
d.text((780, 10), "96 m", font=s, fill="black"); d.text((1660, 480), "54 m", font=s, fill="black")
im.save("floorplan.png")
