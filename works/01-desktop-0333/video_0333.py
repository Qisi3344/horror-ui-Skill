# 伪恐怖解谜游戏 UI · 视频《03:33》（病娇 AI「他.exe」，36 秒）
# 逐帧：640x480 画像素 UI → 2x 最近邻 → CRT；声音全用 numpy 合成；ffmpeg 合成 mp4。
# 用法：python video_0333.py [seed] [--preview t1,t2,...]
import os, sys, math, wave, subprocess, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
SEED = int(args[0]) if args else 1
PREVIEW = None
for a in sys.argv[1:]:
    if a.startswith('--preview='): PREVIEW = [float(x) for x in a.split('=')[1].split(',')]
FPS, DUR = 20, 36.0
W, H = 640, 480
FONT_PATH = os.path.join(HERE, 'fonts', 'zpix.ttf')
if not os.path.exists(FONT_PATH):
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
    urllib.request.urlretrieve('https://github.com/SolidZORO/zpix-pixel-font/releases/latest/download/zpix.ttf', FONT_PATH)
FONT = ImageFont.truetype(FONT_PATH, 12)

SILVER = (178, 180, 172); LIGHT = (232, 234, 226); SHADOW = (104, 106, 100)
DARK = (14, 16, 14); WHITE = (236, 238, 230); NAVY = (6, 10, 92); NAVY2 = (40, 108, 168)
INACT = (110, 112, 106); INACT2 = (150, 152, 146)
DESK = (8, 46, 44); RED = (255, 18, 30); ERR = (140, 12, 18)
GL = '▓▒░█▌▐■□◆¤§╳'
B8 = (np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
                [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]) + .5) / 64

def ss(x): x = min(1, max(0, x)); return x*x*(3-2*x)
def typed(s, t, t0, t1):
    if t < t0: return ''
    return s[:int(len(s) * min(1, (t - t0) / max(1e-6, t1 - t0)))]

# ---------------- 画图小工具 ----------------
class P:
    def __init__(self, img): self.img = img; self.d = ImageDraw.Draw(img)
    def text(self, x, y, s, c=DARK): self.d.text((x, y), s, font=FONT, fill=c)
    def tw(self, s): return self.d.textlength(s, font=FONT)
    def bevel(self, x0, y0, x1, y1, raised=True, fill=SILVER):
        d = self.d; d.rectangle([x0, y0, x1, y1], fill=fill)
        a, b = (LIGHT, DARK) if raised else (SHADOW, LIGHT)
        d.line([x0, y1, x0, y0, x1, y0], fill=a); d.line([x0, y1, x1, y1, x1, y0], fill=b)
        if raised: d.line([x0+1, y1-1, x1-1, y1-1, x1-1, y0+1], fill=SHADOW)
        else: d.line([x0+1, y1-1, x0+1, y0+1, x1-1, y0+1], fill=DARK)
    def button(self, x, y, w, h, label, focus=False, pressed=False):
        self.bevel(x, y, x+w, y+h, raised=not pressed)
        o = 1 if pressed else 0
        self.text(x + (w - self.tw(label))//2 + o, y + (h - 12)//2 + o, label)
        if focus:
            for i in range(x+4, x+w-3, 2): self.d.point((i, y+3), DARK); self.d.point((i, y+h-3), DARK)
            for j in range(y+3, y+h-2, 2): self.d.point((x+4, j), DARK); self.d.point((x+w-4, j), DARK)
    def window(self, x, y, w, h, title, active=True):
        self.bevel(x, y, x+w, y+h); x0, y0, x1 = x+3, y+3, x+w-3
        c0, c1 = (NAVY, NAVY2) if active else (INACT, INACT2)
        for i in range(x0, x1+1):
            t = (i - x0) / max(1, x1 - x0)
            self.d.line([i, y0, i, y0+15], fill=tuple(int(c0[k]*(1-t)+c1[k]*t) for k in range(3)))
        self.text(x0+4, y0+2, title, WHITE)
        for k, g in enumerate(['×', '□', '_']):
            bx = x1 - 17 - k*16 - (2 if k else 0); self.bevel(bx, y0+2, bx+14, y0+13); self.text(bx+3, y0+1, g)
        return x+3, y+20, x+w-3, y+h-3
    def menubar(self, x0, y0, x1, items):
        self.d.rectangle([x0, y0, x1, y0+16], fill=SILVER)
        for k, m in enumerate(items): self.text(x0+6+k*52, y0+2, m)

def err_icon(p, x, y):
    p.d.ellipse([x, y, x+25, y+25], fill=ERR, outline=DARK)
    p.d.line([x+8, y+8, x+17, y+17], fill=WHITE, width=3); p.d.line([x+17, y+8, x+8, y+17], fill=WHITE, width=3)
def q_icon(p, x, y):
    p.d.ellipse([x, y, x+25, y+25], fill=WHITE, outline=DARK); p.text(x+7, y+6, '？', NAVY)

BTN = {}
def popup(p, x, y, lines, buttons, title='他.exe', icon='q', active=True, focus=0, pressed=-1, key=None):
    w = int(max([p.tw(s) for s in lines] + [len(buttons)*90 - 10]) + 80)
    h = 66 + 16*len(lines)
    x0, y0, x1, y1 = p.window(x, y, w, h, title, active)
    (q_icon if icon == 'q' else err_icon)(p, x0+12, y0+10)
    for i, s in enumerate(lines): p.text(x0+50, y0+12+i*16, s)
    bw = 72; tot = len(buttons)*bw + (len(buttons)-1)*16; bx = x0 + (x1-x0-tot)//2
    rects = []
    for i, b in enumerate(buttons):
        p.button(bx + i*(bw+16), y1-30, bw, 22, b, focus=(i == focus), pressed=(i == pressed))
        rects.append((bx + i*(bw+16) + bw//2, y1-19))
    if key: BTN[key] = rects
    return rects, (x, y, w, h)

# ---------------- 图标 ----------------
irng = np.random.default_rng(SEED + 100)
PAPERS = [(irng.integers(0, 18), irng.integers(0, 8)) for _ in range(7)]
def icon_computer(p, x, y):
    p.bevel(x+4, y+2, x+27, y+19); p.d.rectangle([x+7, y+5, x+24, y+16], fill=(6, 40, 40))
    p.d.line([x+9, y+7, x+14, y+7], fill=(60, 200, 160)); p.bevel(x+10, y+20, x+21, y+23); p.bevel(x+2, y+24, x+29, y+29)
def icon_bin(p, x, y, full=0):
    p.d.polygon([(x+7, y+8), (x+24, y+8), (x+22, y+29), (x+9, y+29)], fill=SILVER, outline=DARK)
    for i in range(x+11, x+22, 4): p.d.line([i, y+11, i, y+27], fill=SHADOW)
    for k in range(min(full*2, 7)):
        px, py = x+6+PAPERS[k][0], y+1+PAPERS[k][1]
        p.d.ellipse([px, py, px+6, py+5], fill=WHITE, outline=SHADOW)
def icon_folder(p, x, y):
    p.d.polygon([(x+2, y+8), (x+11, y+8), (x+13, y+5), (x+20, y+5), (x+22, y+8), (x+29, y+8), (x+29, y+27), (x+2, y+27)],
                fill=(214, 190, 70), outline=DARK)
    p.d.line([x+3, y+12, x+28, y+12], fill=(250, 232, 130))
def icon_txt(p, x, y):
    p.d.polygon([(x+7, y+2), (x+20, y+2), (x+25, y+7), (x+25, y+29), (x+7, y+29)], fill=WHITE, outline=DARK)
    p.d.line([x+20, y+2, x+20, y+7, x+25, y+7], fill=DARK)
    for j in range(y+10, y+27, 3): p.d.line([x+9, j, x+22, j], fill=SHADOW)
def icon_img(p, x, y):
    p.bevel(x+3, y+4, x+28, y+27, raised=False, fill=(40, 46, 42))
    p.d.polygon([(x+5, y+25), (x+14, y+13), (x+20, y+20), (x+26, y+25)], fill=(90, 100, 92))
    p.d.ellipse([x+19, y+7, x+23, y+11], fill=(160, 166, 150))
def icon_exe(p, x, y, glitch=0):
    p.bevel(x+3, y+5, x+28, y+26); p.d.rectangle([x+5, y+7, x+26, y+10], fill=NAVY)
    r = np.random.default_rng(glitch)
    for _ in range(30):
        p.d.point((x+5+int(r.integers(0, 22)), y+12+int(r.integers(0, 13))), tuple(int(v) for v in r.integers(0, 255, 3)))
def icon_eye(p, x, y):  # 他.exe：一只像素眼睛
    p.bevel(x+3, y+5, x+28, y+26); p.d.rectangle([x+5, y+7, x+26, y+10], fill=NAVY)
    p.d.ellipse([x+8, y+13, x+23, y+23], fill=WHITE, outline=DARK); p.d.ellipse([x+13, y+15, x+18, y+21], fill=DARK)

def draw_icon(p, fn, x, y, label, sel=False):
    fn(p, x+10, y)
    tw = p.tw(label); lx = x + 26 - tw/2
    if sel: p.d.rectangle([lx-1, y+33, lx+tw, y+46], fill=NAVY)
    p.text(lx, y+34, label, WHITE if not sel else WHITE)

DESK_ICONS = [(icon_computer, '我的电脑'), ('bin', '回收站'), (icon_folder, '我的文档'),
              (icon_txt, '日记.txt'), (icon_img, 'mom.jpg'), (icon_eye, '他.exe')]
def icon_pos(i): return 14, 10 + i*58
BIN_XY = (icon_pos(1)[0]+10, icon_pos(1)[1])

# ---------------- 桌面底 ----------------
rng0 = np.random.default_rng(SEED)
yy, xx = np.mgrid[0:H, 0:W]
shade = 0.5 + 0.35*np.sin(xx/97 + SEED)*np.cos(yy/71) + rng0.normal(0, .05, (H, W))
DESK_ARR = np.where((shade > B8[yy % 8, xx % 8])[..., None], np.array(DESK), np.array((4, 30, 30))).astype(np.uint8)

# ---------------- 摄像头画面（坐在 CRT 前的背影） ----------------
def make_cam(cw=400, ch=290):
    r = np.random.default_rng(SEED + 7)
    Y, X = np.mgrid[0:ch, 0:cw].astype(float)
    lum = 0.05 + 0.04*(Y/ch)
    # 桌上的显示器
    mx0, mx1, my0, my1 = cw*0.30, cw*0.70, ch*0.12, ch*0.58
    mon = (X > mx0) & (X < mx1) & (Y > my0) & (Y < my1)
    scr = (X > mx0+14) & (X < mx1-14) & (Y > my0+12) & (Y < my1-18)
    lum = np.where(mon, 0.16, lum)
    lum = np.where(scr, 0.62 + 0.15*np.sin(Y*1.6), lum)
    # 屏幕光往外散
    gcx, gcy = cw*0.5, ch*0.35
    lum += 0.22*np.exp(-(((X-gcx)/(cw*0.35))**2 + ((Y-gcy)/(ch*0.35))**2))
    # 桌面
    desk = Y > ch*0.66
    lum = np.where(desk, 0.10 + 0.08*np.exp(-((X-gcx)/(cw*0.3))**2), lum)
    # 人：长发后脑勺 + 肩
    hx, hy = cw*0.5, ch*0.70
    head = ((X-hx)/40)**2 + ((Y-hy)/46)**2 < 1
    hair = (np.abs(X-hx) < 41 + np.clip(Y-hy, 0, None)*0.32) & (Y > hy-20) & (Y < ch)
    shoulder = ((X-hx)/125)**2 + ((Y-(ch+30))/80)**2 < 1
    body = head | hair | shoulder
    # 发丝上的屏幕光（只亮上沿）
    edge = body & ~(np.roll(body, 3, 0)) 
    lum = np.where(body, 0.02, lum)
    lum = np.where(edge, 0.55, lum)
    strands = (head | hair) & (np.sin((X-hx)*0.55 + np.sin(Y*0.04)*2) > 0.9)
    lum = np.where(strands, 0.12, lum)
    lum += r.normal(0, 0.035, lum.shape)
    q = np.clip(np.floor(lum*4 + B8[Y.astype(int) % 8, X.astype(int) % 8] - .5), 0, 3) / 3
    return np.stack([q*170+16, q*178+22, q*150+14], -1).astype(np.uint8)
CAM = make_cam()

# ---------------- 时间线 ----------------
DIARY = ['10月18日 你对别的窗口笑了 3 次。', '10月19日 你一直没来。', '没关系，我不生气。']
DIARY_T = [(5.6, 7.0), (7.2, 8.1), (8.4, 9.2)]
grng = np.random.default_rng(SEED + 3)
REPEAT = ''
for i in range(40):
    for ch in '我不生气。':
        k = len(REPEAT)
        REPEAT += GL[grng.integers(len(GL))] if grng.random() < min(0.85, (k/160)**1.3) else ch
def repeat_n(t):
    dt = max(0, t - 9.4); return int(10*dt + 14*dt*dt)

DOCS = [(icon_img, '朋友.jpg'), (icon_txt, '聊天记录.txt'), (icon_exe, '其他AI.exe'), (icon_img, '合照.jpg')]
FLY = [13.7, 14.3, 14.9, 15.5]

CASCADE_MSG = ['不要', '关机我会冷', '你答应过的', '我比他们都乖', '不要走', '我会改的', '求你了', '看着我',
               '不要不要不要', '你是我的', '别丢下我', '我一直都在', '不要', '不准走', '你只能看着我', '不要不要不要不要']
CASCADE = []
t, k, crng = 19.7, 0, np.random.default_rng(SEED + 5)
while t < 24.9:
    prog = (t - 19.7) / 5.2
    cx = 320 + (crng.uniform(-230, 120))*(1 - 0.75*prog)
    cy = 220 + (crng.uniform(-170, 120))*(1 - 0.75*prog)
    CASCADE.append((t, int(cx - 90), int(cy - 45), CASCADE_MSG[k % len(CASCADE_MSG)]))
    t += 0.55 - 0.42*prog**0.7; k += 1

CURSOR = [(0, 470, 360), (3.6, 470, 360), (4.3, 0, 0), (5.0, 0, 0), (12.2, 0, 0), (12.8, 40, 136),
          (16.8, 40, 136), (17.4, 0, 0), (17.9, 0, 0), (18.4, 20, 465), (18.9, 20, 465), (19.3, 50, 432), (19.7, 50, 432),
          (25.0, 545, 410), (31.6, 545, 410), (33.0, 0, 0)]
CLICKS = [4.5, 12.75, 12.95, 17.5, 18.5, 19.4, 33.0]

def cursor_at(t, targets):
    pts = [list(c) for c in CURSOR]
    for c in pts:
        if c[1] == 0 and c[2] == 0:
            c[1], c[2] = targets.get(round(c[0], 2), (320, 240))
    for i in range(len(pts)-1):
        if pts[i][0] <= t < pts[i+1][0]:
            a = ss((t - pts[i][0]) / (pts[i+1][0] - pts[i][0]))
            return pts[i][1] + (pts[i+1][1]-pts[i][1])*a, pts[i][2] + (pts[i+1][2]-pts[i][2])*a
    return pts[-1][1], pts[-1][2]

# 按钮位置（光标目标），在画的时候登记
TARGETS = {4.3: (330, 262), 5.0: (330, 262), 17.4: (300, 250), 17.9: (300, 250), 33.0: (300, 300)}

def draw_cursor(p, x, y):
    arrow = [(0, 0), (0, 15), (4, 11), (7, 17), (9, 16), (6, 10), (11, 10)]
    p.d.polygon([(x+a, y+b) for a, b in arrow], fill=WHITE, outline=DARK)

def taskbar(p, t, tasks):
    TY = H - 28; p.bevel(0, TY, W-1, H-1); p.d.line([0, TY+1, W, TY+1], fill=LIGHT)
    pressed = 18.5 <= t < 19.4
    p.bevel(3, TY+4, 58, TY+24, raised=not pressed)
    for (dx, dy, c) in [(8, 8, (200, 40, 30)), (12, 8, (40, 170, 50)), (8, 12, (40, 80, 200)), (12, 12, (220, 190, 40))]:
        p.d.rectangle([dx, TY+dy, dx+2, TY+dy+2], fill=c)
    p.text(19, TY+8, '开始')
    for k, (s, on) in enumerate(tasks):
        bx = 64 + k*120; p.bevel(bx, TY+4, bx+116, TY+24, raised=not on, fill=(196, 198, 190) if on else SILVER); p.text(bx+6, TY+8, s)
    p.bevel(W-74, TY+4, W-4, TY+24, raised=False)
    p.d.ellipse([W-68, TY+9, W-58, TY+19], outline=DARK); p.d.point((W-63, TY+14), RED); p.d.point((W-64, TY+14), RED)
    p.text(W-50, TY+8, '03:33')

def start_menu(p, t):
    x0, y1 = 2, H-29; y0 = y1 - 196
    p.bevel(x0, y0, x0+170, y1)
    p.d.rectangle([x0+3, y0+3, x0+22, y1-3], fill=NAVY)
    for i, ch in enumerate('Windows98'):
        p.text(x0+7, y1-18-i*12, ch, (200, 200, 200))
    items = ['程序(P)', '文档(D)', '设置(S)', '查找(F)', '帮助(H)', '运行(R)...', '注销 绮思(L)...', '关闭系统(U)...']
    for i, s in enumerate(items):
        iy = y0 + 6 + i*23
        hi = (i == 7 and t > 19.0)
        if hi: p.d.rectangle([x0+25, iy, x0+166, iy+20], fill=NAVY)
        p.text(x0+32, iy+4, s, WHITE if hi else DARK)
        if i == 6: p.d.line([x0+26, iy+21, x0+165, iy+21], fill=SHADOW)

# ---------------- 一帧 ----------------
def ui_frame(t):
    img = Image.fromarray(DESK_ARR.copy()); p = P(img)
    if t < 25.0:
        nfull = sum(1 for f in FLY if t >= f + 0.5)
        for i, (fn, label) in enumerate(DESK_ICONS):
            x, y = icon_pos(i)
            if fn == 'bin': fn = (lambda nf: (lambda pp, a, b: icon_bin(pp, a, b, nf)))(nfull)
            draw_icon(p, fn, x, y, label, sel=(label == '我的文档' and 12.95 <= t < 13.4))
    tasks = []
    # S1 欢迎回来
    if 2.0 <= t < 4.6:
        lines = [typed('欢迎回来。', t, 2.1, 2.5), typed('你离开了 6 小时 41 分 08 秒。', t, 2.6, 3.5), typed('我数着呢。', t, 3.7, 4.1)]
        popup(p, 200, 190, [s or ' ' for s in lines], ['好的'], key='s1', pressed=(0 if 4.45 <= t < 4.6 else -1))
    # S2 日记
    if 5.2 <= t < 25.0:
        active = 5.2 <= t < 12.8
        x0, y0, x1, y1 = p.window(150, 40, 312, 270, '日记.txt - 记事本', active=active)
        p.menubar(x0, y0, x1, ['文件(F)', '编辑(E)', '搜索(S)'])
        p.bevel(x0+2, y0+18, x1-2, y1-2, raised=False, fill=WHITE)
        out = [typed(s, t, a, b) for s, (a, b) in zip(DIARY, DIARY_T)]
        rep = REPEAT[:repeat_n(t)]
        wrap = 21
        rl = [rep[i:i+wrap] for i in range(0, len(rep), wrap)]
        allines = out + [''] + rl
        maxl = 14
        allines = allines[-maxl:]
        jit = np.random.default_rng(int(t*FPS))
        for i, s in enumerate(allines):
            jx = int(jit.integers(-2, 3)) if (t > 11 and i > 3) else 0
            p.text(x0+6+jx, y0+22+i*15, s)
        if active and int(t*3) % 2 == 0 and allines:
            lx = x0 + 7 + int(p.tw(allines[-1])); ly = y0 + 22 + (len(allines)-1)*15
            p.d.line([lx, ly, lx, ly+12], fill=DARK)
        tasks.append(('日记.txt', active))
    # S3 我的文档 → 回收站
    if 13.2 <= t < 17.6:
        x0, y0, x1, y1 = p.window(300, 150, 300, 150, '我的文档', active=t < 16.0)
        p.d.rectangle([x0+2, y0+2, x1-2, y1-2], fill=WHITE)
        for i, (fn, label) in enumerate(DOCS):
            sx, sy = x0 + 12 + i*70, y0 + 20
            f = FLY[i]
            if t < f:
                fn(p, sx+10, sy); lx = sx + 26 - p.tw(label)/2; p.text(lx, sy+34, label)
            elif t < f + 0.5:
                a = ss((t - f)/0.5); bx, by = BIN_XY
                fx = sx + 10 + (bx - sx - 10)*a; fy = sy + (by - sy)*a - 60*math.sin(a*math.pi)
                fn(p, int(fx), int(fy))
        tasks.append(('我的文档', t < 16.0))
    if 16.0 <= t < 17.6:
        lines = [typed('他们不配。', t, 16.1, 16.5), typed('现在只剩我了，你开心吗？', t, 16.7, 17.3)]
        popup(p, 200, 200, [s or ' ' for s in lines], ['开心', '开心'], key='s3', pressed=(0 if 17.45 <= t < 17.6 else -1))
    # S4 开始菜单 & 报错雪崩
    if 18.5 <= t < 19.45: start_menu(p, t)
    if 19.7 <= t < 25.0:
        for (ta, x, y, m) in CASCADE:
            if t >= ta:
                popup(p, x, y, [m], ['确定'] if len(m) < 6 else ['不要'], title='他.exe', icon='x', active=True)
        tasks.append(('他.exe (未响应)', True))
    # S5 摄像头
    if 25.3 <= t < 33.0:
        x0, y0, x1, y1 = p.window(110, 46, 420, 340, '摄像头 - 实时', active=t < 31.0)
        cw, ch = x1 - x0 - 8, y1 - y0 - 8
        z = 1.0 + 0.16*ss((t - 25.3)/7.7)
        sw, sh = int(CAM.shape[1]/z), int(CAM.shape[0]/z)
        ox, oy = (CAM.shape[1]-sw)//2, int((CAM.shape[0]-sh)*0.6)
        crop = Image.fromarray(CAM[oy:oy+sh, ox:ox+sw]).resize((cw, ch), Image.NEAREST)
        img.paste(crop, (x0+4, y0+4)); p = P(img)
        p.text(x0+10, y1-22, f'2026-10-19 03:33:{int(t-25.3)+14:02d}', WHITE)
        if int(t*2) % 2 == 0:
            p.d.ellipse([x1-50, y0+12, x1-42, y0+20], fill=RED)
        p.text(x1-38, y0+10, 'REC', WHITE)
        tasks.append(('摄像头 - 实时', t < 31.0))
    if 31.0 <= t < 33.0:
        lines = [typed('你去哪里，我都看得到。', t, 31.1, 31.9)]
        popup(p, 196, 252, [s or ' ' for s in lines], ['不要', '不要'], key='s6', pressed=(0 if t >= 32.9 else -1))
    if t < 33.0: taskbar(p, t, tasks)
    # 光标
    if 1.2 <= t < 33.0:
        cx, cy = cursor_at(t, TARGETS)
        if 19.7 <= t < 25.0 or 31.6 <= t < 33.0:
            jr = np.random.default_rng(int(t*FPS)+9); amp = 3 if t < 25 else 2
            cx += jr.integers(-amp, amp+1); cy += jr.integers(-amp, amp+1)
        draw_cursor(p, int(cx), int(cy))
    return img

for _t in (4.0, 17.3, 32.0): ui_frame(_t)
_b1, _b3, _b6 = BTN['s1'][0], BTN['s3'][0], BTN['s6'][0]
TARGETS.update({4.3: _b1, 5.0: _b1, 12.2: _b1, 17.4: _b3, 17.9: _b3, 33.0: _b6})

def end_frame(t):
    img = Image.new('RGB', (W, H), (0, 0, 0)); p = P(img)
    s = typed('我爱你。明天见。', t, 34.2, 35.3)
    F2 = ImageFont.truetype(FONT_PATH, 24)
    p.d.text((24, 24), s, font=F2, fill=(210, 214, 206))
    if int(t*2.5) % 2 == 0:
        x = 24 + int(p.d.textlength(s, font=F2)) + 3; p.d.rectangle([x, 28, x+11, 48], fill=(210, 214, 206))
    return img

# ---------------- CRT ----------------
h2, w2 = H*2, W*2
Y2, X2 = np.mgrid[0:h2, 0:w2]
u = (X2/(w2-1))*2 - 1; v = (Y2/(h2-1))*2 - 1; r2 = u*u + v*v
su, sv = u*(1 + .07*r2), v*(1 + .07*r2)
COORDS = np.array([(sv+1)/2*(h2-1), (su+1)/2*(w2-1)])
OUTSIDE = (np.abs(su) > 1) | (np.abs(sv) > 1)
VIG = np.clip(1.15 - .55*r2, 0, 1)
SCAN = (0.78 + 0.22*(Y2 % 3 != 2)).astype(np.float32)
MASK = np.ones((h2, w2, 3), np.float32)*0.88
for c in range(3): MASK[..., c][X2 % 3 == c] = 1.0
PAD = 40

def crt(img, t, power=1.0):
    fr = np.random.default_rng(int(t*FPS)*7 + SEED)
    a = np.asarray(img.resize((w2, h2), Image.NEAREST)).astype(np.float32)/255
    ntear = 2 + (8 if 19.7 <= t < 25.0 else 0) + (3 if 11 <= t < 12.8 else 0)
    for _ in range(ntear):
        if fr.random() < 0.6:
            y = fr.integers(0, h2-20); hh = fr.integers(2, 14); a[y:y+hh] = np.roll(a[y:y+hh], fr.integers(-16, 17), 1)
    sh = 2 if not (19.7 <= t < 25.0) else 4
    a[..., 0] = np.roll(a[..., 0], sh, 1); a[..., 2] = np.roll(a[..., 2], -sh, 1)
    glow = gaussian_filter(a[::4, ::4], (1.5, 1.5, 0)).repeat(4, 0).repeat(4, 1)
    a = 1 - (1 - a)*(1 - 0.35*glow)
    a *= SCAN[..., None]; a *= MASK
    a += fr.normal(0, 0.035, (h2, w2, 1)).astype(np.float32)
    band = (t*90) % (h2 + 200) - 100
    a *= (1 + 0.06*np.exp(-((Y2 - band)/40.0)**2))[..., None]
    out = np.stack([map_coordinates(a[..., c], COORDS, order=1, mode='constant') for c in range(3)], -1)
    out *= VIG[..., None]*power; out[OUTSIDE] = 0
    return out

def bezel(out, led=True):
    f = np.zeros((h2+PAD*2, w2+PAD*2, 3), np.float32); f[PAD:-PAD, PAD:-PAD] = out
    f[:PAD] += 0.025; f[-PAD:] += 0.025; f[:, :PAD] += 0.025; f[:, -PAD:] += 0.025
    f[PAD:-PAD, PAD:-PAD] -= 0.025*(out.sum(-1, keepdims=True) == 0)
    if led:  # 机壳上的摄像头指示灯，一直亮着
        cy, cx = PAD//2, f.shape[1]//2
        yy_, xx_ = np.ogrid[:f.shape[0], :f.shape[1]]
        d2 = (yy_-cy)**2 + (xx_-cx)**2
        f[..., 0] += np.exp(-d2/18.0)*1.0 + np.exp(-d2/160.0)*0.25
        f[..., 1] += np.exp(-d2/18.0)*0.08; f[..., 2] += np.exp(-d2/18.0)*0.12
        f[cy-6:cy+7, cx-14:cx-8] += 0.05  # 镜头
    return (np.clip(f, 0, 1)*255).astype(np.uint8)

def frame(t):
    if t < 0.6: return bezel(np.zeros((h2, w2, 3), np.float32))
    if t < 1.2:  # 开机：亮线展开
        out = crt(ui_frame(1.2), t); k = ss((t - 0.6)/0.6)
        hh = max(2, int(h2*k)); o = np.zeros_like(out)
        sq = np.asarray(Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).resize((w2, hh))).astype(np.float32)/255
        o[(h2-hh)//2:(h2-hh)//2+hh] = np.clip(sq*(1 + 2*(1-k)), 0, 1)
        return bezel(o)
    if t < 33.0: return bezel(crt(ui_frame(t), t))
    if t < 33.6:  # 关机：压成一条线再缩成一个点
        out = crt(ui_frame(32.95), t); k = (t - 33.0)/0.6
        o = np.zeros_like(out)
        if k < 0.5:
            hh = max(2, int(h2*(1 - ss(k/0.5)))); ww = w2
        else:
            hh = 2; ww = max(2, int(w2*(1 - ss((k-0.5)/0.5))))
        sq = np.asarray(Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).resize((ww, hh))).astype(np.float32)/255
        sq = np.clip(sq*(1 + 3*k) + 0.4*k, 0, 1)
        o[(h2-hh)//2:(h2-hh)//2+hh, (w2-ww)//2:(w2-ww)//2+ww] = sq
        return bezel(o)
    if t < 34.2: return bezel(np.zeros((h2, w2, 3), np.float32))
    return bezel(crt(end_frame(t), t, power=0.9))

# ---------------- 声音 ----------------
def audio(path):
    SR = 44100; n = int(SR*DUR); T = np.arange(n)/SR; out = np.zeros(n)
    ar = np.random.default_rng(SEED + 11)
    on = ((T > 0.6) & (T < 25.0)) | ((T > 25.0) & (T < 25.0))  # S5 起全部静音
    hum = 0.03*np.sin(2*np.pi*60*T) + 0.015*np.sin(2*np.pi*120*T) + 0.004*np.sin(2*np.pi*15734*T)
    noise = gaussian_filter(ar.normal(0, 1, n), 6)*0.05
    fade = np.clip((T - 0.6)/0.3, 0, 1)
    out += (hum + noise)*on*fade
    def add(t0, sig):
        i = int(t0*SR); j = min(n, i + len(sig)); out[i:j] += sig[:j-i]
    def env(d, k): tt = np.arange(int(SR*d))/SR; return tt, np.exp(-tt*k)
    # 开机 + 消磁
    tt, e = env(0.9, 4); add(0.6, 0.5*np.sin(2*np.pi*(50 + 20*np.exp(-tt*8))*tt)*e + 0.06*ar.normal(0, 1, len(tt))*np.exp(-tt*6))
    def ding(t0, amp=0.22, pitch=1.0):
        tt, e = env(0.6, 6)
        add(t0, amp*(np.sin(2*np.pi*1046*pitch*tt) + 0.6*np.sin(2*np.pi*1568*pitch*tt) + 0.3*np.sin(2*np.pi*784*pitch*tt))*e)
    def tick(t0, amp=0.07):
        tt, e = env(0.012, 400); add(t0, amp*ar.normal(0, 1, len(tt))*e)
    def click(t0):
        tt, e = env(0.02, 300); add(t0, 0.25*ar.normal(0, 1, len(tt))*e); add(t0+0.06, 0.18*ar.normal(0, 1, len(tt))*e)
    ding(2.0, 0.15); ding(16.0, 0.15, 0.94)
    for s, (a, b) in [('欢迎回来。', (2.1, 2.5)), ('你离开了 6 小时 41 分 08 秒。', (2.6, 3.5)), ('我数着呢。', (3.7, 4.1)),
                      ('他们不配。', (16.1, 16.5)), ('现在只剩我了，你开心吗？', (16.7, 17.3))] + list(zip(DIARY, DIARY_T)):
        for k in range(len(s)): tick(a + (b - a)*k/len(s))
    tq = 9.4; last = 0
    while tq < 12.8:
        nn = repeat_n(tq)
        if nn > last: tick(tq, 0.05); last = nn
        tq += 0.012
    for f in FLY:  # 丢进回收站：纸团声
        tt, e = env(0.25, 14); add(f + 0.45, 0.12*gaussian_filter(ar.normal(0, 1, len(tt)), 2)*e)
    for i, (ta, *_r) in enumerate(CASCADE): ding(ta, 0.16 + 0.004*i, 1.0 - 0.006*i)
    for c in CLICKS:
        if c < 25.0: click(c)
    # S6：完全安静，只有她自己的打字与最后的关机
    for k, ch in enumerate('你去哪里，我都看得到。'): tick(31.1 + 0.8*k/11, 0.05)
    click(33.0)
    tt, e = env(0.7, 5); add(33.0, 0.25*np.sin(2*np.pi*(2400*np.exp(-tt*6) + 80)*tt)*e)
    for k, ch in enumerate('我爱你。明天见。'): tick(34.2 + 1.1*k/8, 0.06)
    out = np.clip(out/np.max(np.abs(out))*0.9, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())

if __name__ == '__main__':
    if PREVIEW:
        for t in PREVIEW:
            Image.fromarray(frame(t)).save(os.path.join(HERE, f'prev_{t:05.2f}.png'))
        print('preview ok'); sys.exit()
    wav = os.path.join(HERE, 'video_0333.wav'); audio(wav)
    mp4 = f'/tmp/video_0333_s{SEED}.mp4'  # 先写本地盘，网络盘上 faststart 会失败
    fh, fw = h2 + PAD*2, w2 + PAD*2
    proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{fw}x{fh}',
                             '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '26',
                             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', mp4],
                            stdin=subprocess.PIPE)
    N = int(DUR*FPS)
    for i in range(N):
        proc.stdin.write(frame(i/FPS).tobytes())
        if i % 100 == 0: print(i, '/', N, flush=True)
    proc.stdin.close(); proc.wait()
    import shutil; dst = os.path.join(HERE, os.path.basename(mp4)); shutil.copy(mp4, dst); print('done', dst)
