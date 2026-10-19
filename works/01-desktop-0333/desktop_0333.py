# 伪恐怖解谜游戏 UI · No.01《03:33》
# 凌晨三点三十三分的 Win98 桌面：日记记事本、走廊照片、报错弹窗层叠、只能点「不要」。
# 先在 640x480 画像素 UI，再最近邻放大 2x，最后加 CRT（扫描线、色散、桶形畸变、撕裂、噪点、暗角）。
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rng = np.random.default_rng(SEED)
W, H = 640, 480
import os, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, 'fonts', 'zpix.ttf')
if not os.path.exists(FONT_PATH):  # 像素中文字体 Zpix（最像素），第一次运行自动下载
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
    urllib.request.urlretrieve('https://github.com/SolidZORO/zpix-pixel-font/releases/latest/download/zpix.ttf', FONT_PATH)
FONT = ImageFont.truetype(FONT_PATH, 12)

# Win98 系统色（略压暗、偏绿，像老显示器）
SILVER = (178, 180, 172); LIGHT = (232, 234, 226); SHADOW = (104, 106, 100)
DARK = (14, 16, 14); WHITE = (236, 238, 230); NAVY = (6, 10, 92); NAVY2 = (40, 108, 168)
INACT = (110, 112, 106); INACT2 = (150, 152, 146)
DESK = (8, 46, 44); RED = (255, 18, 30)

img = Image.new('RGB', (W, H), DESK)
d = ImageDraw.Draw(img)

def text(x, y, s, c=DARK): d.text((x, y), s, font=FONT, fill=c)

def bevel(x0, y0, x1, y1, raised=True, fill=SILVER):
    d.rectangle([x0, y0, x1, y1], fill=fill)
    a, b = (LIGHT, DARK) if raised else (SHADOW, LIGHT)
    d.line([x0, y1, x0, y0, x1, y0], fill=a); d.line([x0, y1, x1, y1, x1, y0], fill=b)
    if raised:
        d.line([x0+1, y1-1, x1-1, y1-1, x1-1, y0+1], fill=SHADOW)
    else:
        d.line([x0+1, y1-1, x0+1, y0+1, x1-1, y0+1], fill=DARK)

def button(x, y, w, h, label, focus=False):
    bevel(x, y, x+w, y+h)
    tw = d.textlength(label, font=FONT)
    text(x + (w - tw)//2, y + (h - 12)//2, label)
    if focus:
        for i in range(x+4, x+w-3, 2):
            d.point((i, y+3), DARK); d.point((i, y+h-3), DARK)
        for j in range(y+3, y+h-2, 2):
            d.point((x+4, j), DARK); d.point((x+w-4, j), DARK)

def titlebar(x0, y0, x1, title, active=True):
    c0, c1 = (NAVY, NAVY2) if active else (INACT, INACT2)
    for i in range(x0, x1+1):
        t = (i - x0) / max(1, x1 - x0)
        d.line([i, y0, i, y0+15], fill=tuple(int(c0[k]*(1-t)+c1[k]*t) for k in range(3)))
    text(x0+4, y0+2, title, WHITE)
    for k, g in enumerate(['×', '□', '_']):
        bx = x1 - 17 - k*16 - (2 if k else 0)
        bevel(bx, y0+2, bx+14, y0+13)
        text(bx+3, y0+1, g)

def window(x, y, w, h, title, active=True):
    bevel(x, y, x+w, y+h)
    d.rectangle([x+1, y+1, x+w-1, y+h-1], outline=SILVER)
    titlebar(x+3, y+3, x+w-3, title, active)
    return x+3, y+20, x+w-3, y+h-3

# ---------- 桌面底：抖动的深青 + 一点不均匀 ----------
B = (np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
               [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]) + .5) / 64
yy, xx = np.mgrid[0:H, 0:W]
shade = 0.5 + 0.35*np.sin(xx/97 + SEED) * np.cos(yy/71) + rng.normal(0, .05, (H, W))
bay = B[yy % 8, xx % 8]
desk = np.where((shade > bay)[..., None], np.array(DESK), np.array((4, 30, 30)))
img.paste(Image.fromarray(desk.astype(np.uint8)))
d = ImageDraw.Draw(img)

# ---------- 桌面图标 ----------
def icon_computer(x, y):
    bevel(x+4, y+2, x+27, y+19); d.rectangle([x+7, y+5, x+24, y+16], fill=(6, 40, 40))
    d.line([x+9, y+7, x+14, y+7], fill=(60, 200, 160))
    bevel(x+10, y+20, x+21, y+23); bevel(x+2, y+24, x+29, y+29)
def icon_bin(x, y):
    d.polygon([(x+7, y+8), (x+24, y+8), (x+22, y+29), (x+9, y+29)], fill=SILVER, outline=DARK)
    for i in range(x+11, x+22, 4): d.line([i, y+11, i, y+27], fill=SHADOW)
    for k in range(6):  # 塞满的纸团
        px, py = x+6+rng.integers(0, 18), y+1+rng.integers(0, 8)
        d.ellipse([px, py, px+6, py+5], fill=WHITE, outline=SHADOW)
def icon_folder(x, y):
    d.polygon([(x+2, y+8), (x+11, y+8), (x+13, y+5), (x+20, y+5), (x+22, y+8), (x+29, y+8), (x+29, y+27), (x+2, y+27)],
              fill=(214, 190, 70), outline=DARK)
    d.line([x+3, y+12, x+28, y+12], fill=(250, 232, 130))
def icon_txt(x, y, scrawl=False):
    d.polygon([(x+7, y+2), (x+20, y+2), (x+25, y+7), (x+25, y+29), (x+7, y+29)], fill=WHITE, outline=DARK)
    d.line([x+20, y+2, x+20, y+7, x+25, y+7], fill=DARK)
    for j in range(y+10, y+27, 3):
        if scrawl: d.line([x+9, j, x+9+rng.integers(6, 15), j+rng.integers(-1, 2)], fill=DARK)
        else: d.line([x+9, j, x+22, j], fill=SHADOW)
def icon_exe(x, y):
    bevel(x+3, y+5, x+28, y+26); d.rectangle([x+5, y+7, x+26, y+10], fill=NAVY)
    for _ in range(30):  # 坏掉的图标：像素噪点
        px, py = x+5+rng.integers(0, 22), y+12+rng.integers(0, 13)
        d.point((px, py), tuple(int(v) for v in rng.integers(0, 255, 3)))
def icon_img(x, y):
    bevel(x+3, y+4, x+28, y+27, raised=False, fill=(40, 46, 42))
    d.polygon([(x+5, y+25), (x+14, y+13), (x+20, y+20), (x+26, y+25)], fill=(90, 100, 92))
    d.ellipse([x+19, y+7, x+23, y+11], fill=(160, 166, 150))

icons = [(icon_computer, '我的电脑'), (icon_bin, '回收站'), (icon_folder, '我的文档'),
         (icon_txt, '日记.txt'), (icon_img, 'mom.jpg'), (lambda x, y: icon_txt(x, y, True), '不要打开.txt'), (icon_exe, '他.exe')]
for i, (fn, label) in enumerate(icons):
    x, y = 14, 10 + i*58
    fn(x+10, y)
    tw = d.textlength(label, font=FONT)
    lx = x + 26 - tw/2
    if label == '他.exe':  # 被选中
        d.rectangle([lx-1, y+33, lx+tw, y+46], fill=NAVY)
        for px in range(x+10, x+42, 2):
            for py in range(y, y+30, 2):
                if img.getpixel((px, py)) != tuple(desk[py, px]):
                    d.point((px, py), NAVY)
    text(lx, y+34, label, WHITE)

# ---------- 走廊照片：mom.jpg ----------
ax0, ay0, ax1, ay1 = window(318, 28, 296, 236, 'mom.jpg - 图像预览', active=False)
d.rectangle([ax0, ay0, ax1, ay0+16], fill=SILVER)
for k, m in enumerate(['文件(F)', '查看(V)', '帮助(H)']): text(ax0+6+k*52, ay0+2, m)
px0, py0, px1, py1 = ax0+6, ay0+22, ax1-6, ay1-22
bevel(px0-2, py0-2, px1+2, py1+2, raised=False, fill=DARK)
pw, ph = px1-px0, py1-py0
Y, X = np.mgrid[0:ph, 0:pw].astype(float)
cx, cy = pw*0.52, ph*0.44
nx, ny = (X-cx)/pw, (Y-cy)/ph
door_w, door_h = 30, 58
# 透视：离消失点越近越黑
depth = np.maximum(np.abs(nx)*2.0, np.abs(ny)*2.2)
lum = 0.08 + 0.85*np.clip(depth,0,1)**0.9
floor = ny > 0.17*np.abs(nx)/0.5 * 0 + 0.0
lum = np.where((ny > np.abs(nx)*1.35) & (ny > 0), lum*0.8 + 0.05*((np.round((1/(ny+.02))*3) % 2)), lum)  # 地板木条
lum = np.where((np.abs(nx) > np.abs(ny)/1.36), lum*(0.9 + 0.1*np.sin(Y*0.9)), lum)  # 墙纸条纹
inner = (np.abs(X-cx) < door_w/2) & (Y > cy-door_h/2) & (Y < cy+door_h/2)
lum = np.where(inner, 0.2, lum)
# 门里站着的人
fx = cx + 1
fig = ((X-fx)**2/30 + (Y-(cy-14))**2/36 < 1) | ((np.abs(X-fx) < 6 + (Y-(cy-8))*0.18) & (Y > cy-9) & (Y < cy+door_h/2))
lum = np.where(fig & inner, 0.0, lum)
# 门框微光
frame = (np.abs(np.abs(X-cx)-door_w/2-1) < 1) & (Y > cy-door_h/2-1) & (Y < cy+door_h/2)
lum = np.where(frame, 0.05, lum)
lum += rng.normal(0, 0.035, lum.shape)
q = np.clip(np.floor(lum*4 + B[Y.astype(int) % 8, X.astype(int) % 8] - .5), 0, 3) / 3
photo = np.stack([q*170+16, q*176+20, q*150+14], -1)
# JPEG 坏块：几块错位
for _ in range(6):
    by = rng.integers(0, ph-8)//8*8; bx = rng.integers(0, pw-48)//8*8; bw = rng.integers(2, 6)*8
    photo[by:by+8, bx:bx+bw] = np.roll(photo[by:by+8, bx:bx+bw], rng.integers(3, 20), 1)*0.8 + 20
img.paste(Image.fromarray(np.clip(photo, 0, 255).astype(np.uint8)), (px0, py0))
d = ImageDraw.Draw(img)
# 唯一红色：门里那双眼睛
ex, ey = int(px0 + fx), int(py0 + cy - 15)
d.rectangle([ex-4, ey, ex-3, ey], fill=RED); d.rectangle([ex+2, ey, ex+3, ey], fill=RED)
text(ax0+6, ay1-17, '拍摄于 1998-10-19 03:33', SHADOW)
text(ax1-58, ay1-17, '1 / 1', SHADOW)

# ---------- 记事本：日记.txt ----------
nx0, ny0, nx1, ny1 = window(96, 70, 262, 250, '日记.txt - 记事本', active=False)
d.rectangle([nx0, ny0, nx1, ny0+16], fill=SILVER)
for k, m in enumerate(['文件(F)', '编辑(E)', '搜索(S)']): text(nx0+6+k*52, ny0+2, m)
bevel(nx0+2, ny0+18, nx1-2, ny1-2, raised=False, fill=WHITE)
bevel(nx1-17, ny0+20, nx1-4, ny1-4, fill=(206, 208, 200))
bevel(nx1-17, ny0+20, nx1-4, ny0+33); bevel(nx1-17, ny1-17, nx1-4, ny1-4)
bevel(nx1-17, ny1-60, nx1-4, ny1-30)
lines = ['10月17日 今天和她一起画画了。', '她画了一只小狼，我画了猫头鹰。', '', '10月18日 她说明天还会来。',
         '', '10月19日 她没有来。', '10月19日 她没有来。', '10月19日 她没有来。', '10月19日 她没有来',
         '10月19日 她没有', '10月19日 她', '10月19日', '1O月1g日 门 没 有 锁', '我 在 门 后 面 等']
GL = '▓▒░█▌▐■□◆¤§╳'
for i, s in enumerate(lines):
    yy0 = ny0 + 22 + i*14
    if i >= 12:
        s = ''.join(ch if rng.random() > .25 else GL[rng.integers(len(GL))] for ch in s)
    text(nx0+6 + (rng.integers(-2, 3) if i >= 11 else 0), yy0, s, DARK)
d.line([nx0+6+int(d.textlength(lines[-1], font=FONT))+3, ny0+22+13*14, nx0+6+int(d.textlength(lines[-1], font=FONT))+3, ny0+34+13*14], fill=DARK, width=1)

# ---------- 报错弹窗层叠 ----------
msgs = ['系统找不到指定的人：绮思', '系统找不到指定的人：绮思', '无法关闭“他.exe”：程序没有响应',
        '无法关闭“他.exe”：程序没有响应', '“他.exe”正在使用 摄像头', '你要去哪里？']
def err_icon(x, y):
    d.ellipse([x, y, x+25, y+25], fill=(150, 10, 16), outline=DARK)
    d.line([x+8, y+8, x+17, y+17], fill=WHITE, width=3); d.line([x+17, y+8, x+8, y+17], fill=WHITE, width=3)
def q_icon(x, y):
    d.ellipse([x, y, x+25, y+25], fill=WHITE, outline=DARK)
    text(x+9, y+6, '？', NAVY)
for k, m in enumerate(msgs):
    last = k == len(msgs)-1
    wx, wy = 250 + k*22, 222 + k*20
    w = 236
    x0, y0, x1, y1 = window(wx, wy, w, 104, '他.exe' if last else '错误', active=last)
    (q_icon if last else err_icon)(x0+12, y0+12)
    text(x0+48, y0+18, m)
    if last:
        button(x0+34, y1-30, 72, 22, '不要', focus=True); button(x0+124, y1-30, 72, 22, '不要')
    else:
        button(x0+(x1-x0)//2-36, y1-30, 72, 22, '确定')

# ---------- 任务栏 ----------
TY = H - 28
bevel(0, TY, W-1, H-1)
d.line([0, TY+1, W, TY+1], fill=LIGHT)
bevel(3, TY+4, 58, TY+24)
d.rectangle([8, TY+8, 10, TY+10], fill=(200, 40, 30)); d.rectangle([12, TY+8, 14, TY+10], fill=(40, 170, 50))
d.rectangle([8, TY+12, 10, TY+14], fill=(40, 80, 200)); d.rectangle([12, TY+12, 14, TY+14], fill=(220, 190, 40))
text(19, TY+8, '开始')
for k, (t, on) in enumerate([('日记.txt', False), ('mom.jpg', False), ('他.exe (未响应)', True)]):
    bx = 64 + k*120
    bevel(bx, TY+4, bx+116, TY+24, raised=not on, fill=(196, 198, 190) if on else SILVER)
    text(bx+6, TY+8, t)
bevel(W-74, TY+4, W-4, TY+24, raised=False)
d.ellipse([W-68, TY+9, W-58, TY+19], outline=DARK); d.point((W-63, TY+13), RED)  # 托盘：摄像头亮着
text(W-50, TY+8, '03:33')

# ---------- 鼠标 ----------
mx, my = 330, 422
arrow = [(0, 0), (0, 15), (4, 11), (7, 17), (9, 16), (6, 10), (11, 10)]
d.polygon([(mx+a, my+b) for a, b in arrow], fill=WHITE, outline=DARK)

# ================= CRT =================
big = img.resize((W*2, H*2), Image.NEAREST)
a = np.asarray(big).astype(float) / 255
h2, w2 = a.shape[:2]
# 撕裂：几条横带错位
for _ in range(7):
    y = rng.integers(0, h2-20); hh = rng.integers(2, 14); s = rng.integers(-18, 19)
    a[y:y+hh] = np.roll(a[y:y+hh], s, 1)
# 色散
a[..., 0] = np.roll(a[..., 0], 2, 1); a[..., 2] = np.roll(a[..., 2], -2, 1)
# 光晕
from scipy.ndimage import gaussian_filter, map_coordinates
glow = gaussian_filter(a, (6, 6, 0))
a = 1 - (1 - a) * (1 - 0.35*glow)
# 扫描线 + 荧光点阵
Y2, X2 = np.mgrid[0:h2, 0:w2]
a *= (0.78 + 0.22*(Y2 % 3 != 2))[..., None]
mask = np.ones((h2, w2, 3)) * 0.88
for c in range(3): mask[..., c][X2 % 3 == c] = 1.0
a *= mask
# 噪点 + 滚动亮带
a += rng.normal(0, 0.035, (h2, w2, 1))
a *= (1 + 0.06*np.exp(-((Y2 - h2*0.63)/40.0)**2))[..., None]
# 桶形畸变 + 暗角
u = (X2/(w2-1))*2 - 1; v = (Y2/(h2-1))*2 - 1
r2 = u*u + v*v
k = 0.07
su, sv = u*(1 + k*r2), v*(1 + k*r2)
coords = [((sv+1)/2*(h2-1)), ((su+1)/2*(w2-1))]
out = np.stack([map_coordinates(a[..., c], coords, order=1, mode='constant', cval=0) for c in range(3)], -1)
out *= np.clip(1.15 - 0.55*r2, 0, 1)[..., None]
out[(np.abs(su) > 1) | (np.abs(sv) > 1)] = 0
# 屏幕外的机壳黑边 + 圆角
pad = 40
final = np.zeros((h2+pad*2, w2+pad*2, 3)); final[pad:-pad, pad:-pad] = out
Image.fromarray((np.clip(final, 0, 1)*255).astype(np.uint8)).save(
    os.path.join(HERE, f'desktop_0333_s{SEED}.png'))
print('ok')
