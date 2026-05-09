import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from PIL import Image, ImageDraw, ImageFont

with open("/Users/vas/CLAUDECODE/happ_url.txt") as f:
    URL = f.read().strip()

print(f"URL length: {len(URL)} chars")

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=2,
)
qr.add_data(URL)
qr.make(fit=True)
print(f"QR version: {qr.version}, modules: {qr.modules_count}")

qr_img = qr.make_image(
    image_factory=StyledPilImage,
    module_drawer=RoundedModuleDrawer(),
    color_mask=RadialGradiantColorMask(
        back_color=(255, 255, 255),
        center_color=(30, 80, 200),
        edge_color=(100, 20, 180),
    ),
)

QR_SIZE = 340
TOTAL_W = 400
TOTAL_H = 460

qr_img = qr_img.convert("RGBA").resize((QR_SIZE, QR_SIZE), Image.LANCZOS)

# Фон: вертикальный градиент белый → нежно-фиолетовый
canvas = Image.new("RGBA", (TOTAL_W, TOTAL_H), (255, 255, 255, 255))
draw = ImageDraw.Draw(canvas)
for y in range(TOTAL_H):
    t = y / TOTAL_H
    r = int(248 - t * 18)
    g = int(248 - t * 28)
    b = 255
    draw.line([(0, y), (TOTAL_W, y)], fill=(r, g, b, 255))

# Белый скруглённый фрейм
margin = 10
frame_x = (TOTAL_W - QR_SIZE) // 2 - margin
frame_y = (TOTAL_W - QR_SIZE) // 2 - margin
frame_w = QR_SIZE + margin * 2
frame_h = QR_SIZE + margin * 2

draw.rounded_rectangle(
    [frame_x, frame_y, frame_x + frame_w, frame_y + frame_h],
    radius=20,
    fill=(255, 255, 255, 245),
    outline=(200, 180, 240, 255),
    width=2,
)

qr_x = (TOTAL_W - QR_SIZE) // 2
qr_y = (TOTAL_W - QR_SIZE) // 2
canvas.paste(qr_img, (qr_x, qr_y), qr_img)

draw = ImageDraw.Draw(canvas)
try:
    font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
except Exception:
    font_label = ImageFont.load_default()
    font_badge = font_label

# Надпись внизу
label = "для приложения Happ"
bbox = draw.textbbox((0, 0), label, font=font_label)
tw = bbox[2] - bbox[0]
tx = (TOTAL_W - tw) // 2
ty = qr_y + QR_SIZE + 18

draw.text((tx + 1, ty + 1), label, font=font_label, fill=(150, 100, 200, 100))
draw.text((tx, ty), label, font=font_label, fill=(55, 35, 155, 255))

# Бейдж HAPP вверху
badge_text = "HAPP"
b_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
bw = b_bbox[2] - b_bbox[0] + 22
bh = b_bbox[3] - b_bbox[1] + 10
bx = (TOTAL_W - bw) // 2
by = 14
draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=(75, 35, 175, 230))
draw.text((bx + 11, by + 5), badge_text, font=font_badge, fill=(255, 255, 255, 255))

out_path = "/Users/vas/CLAUDECODE/happ_qr.png"
canvas.convert("RGB").save(out_path, "PNG", dpi=(150, 150))
print(f"Saved: {out_path}")
