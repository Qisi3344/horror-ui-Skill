# win98_horror.py — 凌晨 03:33 Win98 恐怖桌面，纯代码渲染 (Pillow)
from PIL import Image, ImageDraw, ImageFont
import random

random.seed(333)
W, H = 1600, 1000

TEAL = (0, 128, 128); FACE = (192, 192, 192); LIGHT = (255, 255, 255)
MID = (128, 128, 128); DARK = (64, 64, 64); BLACK = (0, 0, 0)
TA = (0, 0, 128); TB = (16, 132, 208)
BLOOD = (122, 13, 13); BLOOD_D = (66, 6, 6)

SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
DEJA_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def F(path, size, idx=2):
    return ImageFont.truetype(path, size, index=idx)

f_title = F(SANS_B, 19); f_text = F(SERIF_B, 17); f_btn = F(SANS_R, 16)
f_small = F(SANS_R, 14); f_clock = F(SANS_B, 16); f_glyph = ImageFont.truetype(DEJA_B, 15)

img = Image.new("RGB", (W, H), TEAL)
d = ImageDraw.Draw(img)

def bevel(x0, y0, x1, y1, w=2, raised=True):
    hi, lo = (LIGHT, DARK) if raised else (DARK, LIGHT)
    for i in range(w):
        d.line([(x0 + i, y0 + i), (x1 - i, y0 + i)], fill=hi)
        d.line([(x0 + i, y0 + i), (x0 + i, y1 - i)], fill=hi)
        d.line([(x0 + i, y1 - i), (x1 - i, y1 - i)], fill=lo)
        d.line([(x1 - i, y0 + i), (x1 - i, y1 - i)], fill=lo)

def title_gradient(x, y, w, active=True):
    a, b = (TA, TB) if active else (MID, FACE)
    for i in range(w):
        t = i / max(w - 1, 1)
        c = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
        d.line([(x + i, y), (x + i, y + 26)], fill=c)

def center_text(cx, y, s, font, fill):
    bb = d.textbbox((0, 0), s, font=font)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y), s, font=font, fill=fill)

def icon_warn(x, y):
    d.polygon([(x + 16, y + 2), (x + 30, y + 29), (x + 2, y + 29)], fill=(255, 255, 0), outline=BLACK)
    d.line([(x + 16, y + 2), (x + 16, y + 2)], fill=BLACK, width=3)
    center_text(x + 16, y + 8, "!", ImageFont.truetype(DEJA_B, 17), BLACK)

def icon_error(x, y, cracked=False):
    d.ellipse([x + 2, y + 2, x + 30, y + 30], fill=(192, 0, 0), outline=BLACK)
    d.line([(x + 10, y + 10), (x + 22, y + 22)], fill=LIGHT, width=4)
    d.line([(x + 22, y + 10), (x + 10, y + 22)], fill=LIGHT, width=4)
    if cracked:
        d.line([(x + 4, y + 6), (x + 12, y + 14), (x + 9, y + 20), (x + 18, y + 28)],
               fill=BLACK, width=2)

def button(x, y, w, label, default=False, disabled=False, h=34):
    d.rectangle([x, y, x + w, y + h], fill=FACE)
    bevel(x, y, x + w, y + h, w=2, raised=True)
    if default:
        d.rectangle([x + 3, y + 3, x + w - 3, y + h - 3], outline=BLACK, width=1)
    fill = MID if disabled else BLACK
    bb = d.textbbox((0, 0), label, font=f_btn)
    d.text((x + (w - (bb[2] - bb[0])) / 2 - bb[0], y + (h - (bb[3] - bb[1])) / 2 - bb[1]),
           label, font=f_btn, fill=fill)

def dialog(x, y, w, h, title, active, icon, lines, buttons, glitch_title=False, blood=False):
    d.rectangle([x, y, x + w, y + h], fill=FACE)
    d.rectangle([x, y, x + w, y + h], outline=DARK, width=1)
    bevel(x + 2, y + 2, x + w - 2, y + h - 2, w=2, raised=True)
    title_gradient(x + 5, y + 5, w - 10, active)
    if glitch_title:  # 标题轻微色散
        for dx, c in [(-2, (255, 60, 60)), (2, (60, 220, 220))]:
            d.text((x + 12 + dx, y + 6), title, font=f_title, fill=c)
    d.text((x + 12, y + 6), title, font=f_title, fill=LIGHT)
    # 关闭按钮
    bx = x + w - 32
    d.rectangle([bx, y + 7, bx + 22, y + 27], fill=FACE)
    bevel(bx, y + 7, bx + 22, y + 27, w=2, raised=True)
    center_text(bx + 11, y + 6, "×", f_glyph, BLACK)
    # 图标 + 文字
    if icon == "warn":
        icon_warn(x + 30, y + 62)
    else:
        icon_error(x + 30, y + 62, cracked=(icon == "crack"))
    tx = x + 84
    ty = y + 64
    for ln in lines:
        d.text((tx, ty), ln, font=f_text, fill=BLACK)
        ty += 30
    # 按钮右下
    by = y + h - 56
    total = sum(b[1] for b in buttons) + 14 * (len(buttons) - 1)
    bx = x + w - 24 - total
    for label, bw, *opt in buttons:
        kw = dict(opt[0]) if opt else {}
        button(bx, by, bw, label, **kw)
        bx += bw + 14
    if blood:  # 窗底渗血
        d.rectangle([x + 4, y + h - 6, x + w - 4, y + h - 3], fill=BLOOD_D)
        for _ in range(9):
            dx = x + random.randint(20, w - 30)
            ln = random.randint(18, 64); wd = random.randint(7, 13)
            d.rounded_rectangle([dx, y + h - 4, dx + wd, y + h - 4 + ln], radius=wd // 2, fill=BLOOD)
            d.line([(dx + 2, y + h), (dx + 2, y + h + ln - 6)], fill=(160, 40, 40))

# —— 桌面图标 ——
def desktop_icon(x, y, kind, label):
    if kind == "pc":
        d.rectangle([x + 6, y, x + 42, y + 30], fill=(0, 0, 128), outline=LIGHT)
        d.rectangle([x + 10, y + 4, x + 38, y + 26], fill=(0, 180, 180))
        d.rectangle([x + 20, y + 30, x + 28, y + 38], fill=FACE)
        d.rectangle([x + 12, y + 38, x + 36, y + 42], fill=FACE)
    else:
        d.polygon([(x + 8, y + 6), (x + 40, y + 6), (x + 36, y + 40), (x + 12, y + 40)], fill=MID, outline=LIGHT)
        for lx in (18, 26, 34):
            d.line([(x + lx, y + 10), (x + lx - 2, y + 36)], fill=DARK)
    bb = d.textbbox((0, 0), label, font=f_small)
    d.text((x + 24 - (bb[2] - bb[0]) / 2 - bb[0] + 1, y + 49), label, font=f_small, fill=BLACK)
    d.text((x + 24 - (bb[2] - bb[0]) / 2 - bb[0], y + 48), label, font=f_small, fill=LIGHT)

desktop_icon(48, 44, "pc", "我的电脑")
desktop_icon(48, 150, "bin", "回收站")

# —— 三层弹窗（由远及近）——
dialog(150, 170, 450, 250, "系统警告", False, "warn",
       ["内存不足。", "无法忘记 03:33 发生的事。"],
       [("确定", 104, {"default": True}), ("取消", 104)])
dialog(600, 300, 500, 270, "错误 333", False, "error",
       ["检测到未知进程", "正在注视你。"],
       [("求救", 104, {"default": True}), ("忽略", 104, {"disabled": True})])
dialog(1010, 130, 470, 310, "致命异常 0E", True, "crack",
       ["你的倒影比你慢了 0.5 秒…▓", "请不要回头。"],
       [("确定", 104, {"disabled": True})],
       glitch_title=True, blood=True)

# —— 鼠标箭头 ——
mx, my = 760, 620
d.polygon([(mx, my), (mx, my + 34), (mx + 9, my + 26), (mx + 14, my + 36),
           (mx + 18, my + 34), (mx + 13, my + 24), (mx + 22, my + 24)],
          fill=LIGHT, outline=BLACK)

# —— 任务栏 ——
tb_y = H - 46
d.rectangle([0, tb_y, W, H], fill=FACE)
d.line([(0, tb_y), (W, tb_y)], fill=LIGHT, width=2)
d.line([(0, tb_y + 2), (W, tb_y + 2)], fill=LIGHT)
# 开始按钮
d.rectangle([8, tb_y + 7, 118, tb_y + 39], fill=FACE)
bevel(8, tb_y + 7, 118, tb_y + 39, w=2, raised=True)
for i, c in enumerate([(255, 0, 0), (0, 160, 0), (0, 0, 200), (220, 200, 0)]):
    d.rectangle([20 + (i % 2) * 11, tb_y + 14 + (i // 2) * 9, 29 + (i % 2) * 11, tb_y + 21 + (i // 2) * 9], fill=c)
d.text((48, tb_y + 12), "开始", font=f_clock, fill=BLACK)
# 任务按钮
for i, t in enumerate(["系统警告", "错误 333", "致命异常 0E"]):
    bx = 130 + i * 190
    d.rectangle([bx, tb_y + 7, bx + 180, tb_y + 39], fill=FACE)
    bevel(bx, tb_y + 7, bx + 180, tb_y + 39, w=2, raised=(i != 2))
    d.text((bx + 12, tb_y + 12), t, font=f_small, fill=BLACK)
# 时钟托盘
d.rectangle([W - 130, tb_y + 7, W - 8, tb_y + 39], fill=FACE)
bevel(W - 130, tb_y + 7, W - 8, tb_y + 39, w=2, raised=False)
center_text(W - 69, tb_y + 11, "03:33", f_clock, BLACK)

# —— CRT 效果：扫描线 + 暗角 + 坏点 ——
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(ov)
for yy in range(0, H, 3):
    od.line([(0, yy), (W, yy)], fill=(0, 0, 0, 16))
import math
for yy in range(0, H, 8):
    for xx in range(0, W, 8):
        dx, dy = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
        v = min(1.0, dx * dx + dy * dy)
        if v > 0.55:
            od.rectangle([xx, yy, xx + 8, yy + 8], fill=(0, 0, 0, int((v - 0.55) * 130)))
img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
d = ImageDraw.Draw(img)
for _ in range(14):  # 坏点
    d.rectangle([random.randint(0, W - 2), random.randint(0, tb_y - 2)] * 2, fill=random.choice([BLACK, LIGHT]))

img.save("/tmp/horror_example.png")
print("saved", img.size)
