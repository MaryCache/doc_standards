"""doc_standards のロゴを、ラフの画像から測った値で組み直して SVG にする。

ラフ（raw/doc_standards-rough.png）は画像生成で作った絵で、線の縁が揺れている。
なぞると揺れまで写るので、部品ごとに次のやり方で起こす。

- 前の紙・折り返し・縦の線と丸・3本の棒: 断面で測った値で図形として組む
- 後ろの2枚の紙: 大きな面なので、色の範囲をぼかしてならしてからなぞる
- 文字: Nunito（SIL OFL 1.1）の字形。ラフの字は揺れがあり、書体で組み直す
- doc を貫く線と丸: 文字の位置から置き直す

座標はラフの画像の画素（2172×724）。最後に余白を付けて切り抜く。

使い方:
    python build_logo.py <Nunito の可変フォント .ttf>
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

HERE = Path(__file__).resolve().parent
LOGO = HERE.parent
RAW = LOGO / 'raw' / 'doc_standards-rough.png'
sys.path.insert(0, str(Path.home() / 'design-library/tools/logo-lab/trace'))
import trace as T  # noqa: E402  logo-lab の当てはめ（fit_closed・segments_to_d）

# ラフから拾った色。trace の色分けの結果をそのまま使う
NAVY, TEAL, BLUE, GRAY, LIGHT, WHITE = '#2A3B50', '#00ACBD', '#3F97E0', '#819EBD', '#A6D3F8', '#FFFFFF'
TEXT_DARK = '#E6EDF3'  # 暗い地で文字に使う色（GitHub のダークモードの文字色）

# --- 前の紙（断面で測った値） ---
PAGE = dict(x0=266, y0=175, x1=548, y1=490)  # 枠の外側
STROKE = 15                                   # 枠の太さ
RADIUS = 40                                   # 外側の角の丸み
FOLD = 289                                    # 折り返しの斜辺（枠の中心線）は x - y = 289。45° で切れている

# --- 縦の線と丸・棒 ---
NODE_X = 340.5
NODE_Y = (293.0, 358.5, 424.0)  # 間隔は 65.5。ラフの 293・358.5・424.5 をそろえた
RING_R, RING_W = 16.5, 13       # 輪は外径 23・内径 10
DOT_R = 22.5                    # まん中のティールの丸
BAR = dict(x0=385, x1=498, h=19.5)  # 棒の中心はラフでは丸より 2〜3px ずれていたので、丸の高さにそろえた

# --- 文字 ---
BASELINE, X_HEIGHT = 441, 121  # ラフの s の下端と上端から
TEXT_X0 = 586                  # ラフの d の左端
WGHT = 850                     # ラフの線の太さに合わせて選んだ（800 は細く、900 は太かった）
TRACK = 12                     # 字間を足す量（字の単位。1000 で1字ぶん）
GAP = 6                        # 輪のまわりで文字を抜く幅


def rounded_poly(pts, radii):
    """多角形の角を円弧で丸めたパス。radii は頂点ごとの半径。"""
    n = len(pts)
    pts = [np.array(p, float) for p in pts]
    d = ''
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        r = radii[i]
        a, b = p0 - p1, p2 - p1
        la, lb = np.linalg.norm(a), np.linalg.norm(b)
        a, b = a / la, b / lb
        ang = np.arccos(np.clip(a @ b, -1, 1))
        t = r / np.tan(ang / 2)  # 角から円弧の端までの長さ
        s, e = p1 + a * t, p1 + b * t
        sweep = 1 if a[0] * b[1] - a[1] * b[0] < 0 else 0
        d += ('M' if i == 0 else 'L') + f'{s[0]:.2f} {s[1]:.2f}'
        d += f'A{r} {r} 0 0 {sweep} {e[0]:.2f} {e[1]:.2f}'
    return d + 'Z'


def page_outline(inset):
    """前の紙の外形（折り返しで右上を切った角丸の形）。inset だけ内側へ縮める。"""
    x0, y0 = PAGE['x0'] + inset, PAGE['y0'] + inset
    x1, y1 = PAGE['x1'] - inset, PAGE['y1'] - inset
    # 斜辺は外側の縁で x - y = FOLD + STROKE/2·√2。inset ぶん内側へ平行移動する
    k = FOLD + (STROKE / 2 - inset) * np.sqrt(2)
    r = max(RADIUS - inset, 1)
    rf = max(12 - inset * 0.5, 2)  # 斜辺の両端の丸み
    pts = [(x0, y0), (y0 + k, y0), (x1, x1 - k), (x1, y1), (x0, y1)]
    return rounded_poly(pts, [r, rf, rf, r, r])


def ring(cx, cy, r, w, color):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{w}"/>'


def smooth_trace(mask, sigma=4.0, err=2.0):
    """面の揺れをならしてからなぞる。細い部品には使わない（丸と線がくっつく）。"""
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma) > 0.5
    d = ''
    for c in T.contours(soft, min_area=200):
        d += T.segments_to_d(T.fit_closed(T._to_edge(c['outer'], soft), err))
        d += ''.join(T.segments_to_d(T.fit_closed(T._to_edge(h, soft), err)) for h in c['holes'])
    return d


def labels():
    """ラフの画素を6色のどれに近いかで分ける（OKLab の代わりに CIELab で十分）。"""
    a = np.asarray(Image.open(RAW).convert('RGB')).astype(np.float32)
    pal = np.array([[255, 255, 255], [0x2A, 0x3B, 0x50], [0x00, 0xAC, 0xBD],
                    [0x3F, 0x97, 0xE0], [0x81, 0x9E, 0xBD], [0xA6, 0xD3, 0xF8]], np.float32)
    lab = lambda x: cv2.cvtColor((x / 255).reshape(-1, 1, 3), cv2.COLOR_RGB2Lab).reshape(-1, 3)
    return ((lab(a)[:, None] - lab(pal)[None]) ** 2).sum(-1).argmin(1).reshape(a.shape[:2])


def back_pages(lbl):
    """後ろの2枚。見えている範囲をなぞる。

    前の紙に接する縁は、ラフのすき間の揺れをそのまま持っている。そこで前の紙のまわり（半径 12）まで
    面を伸ばしてからなぞり、描くときにすき間（半径 14）の形で抜く。伸ばした分は抜く範囲に収まるので
    見えず、見える縁はすき間の形そのものになる。
    """
    h, w = lbl.shape
    xs = np.arange(w)[None, :].repeat(h, 0)
    ys = np.arange(h)[:, None].repeat(w, 1)
    navy = ((lbl == 1) & (xs < 560)).astype(np.uint8)
    _, comp, st, _ = cv2.connectedComponentsWithStats(navy)
    ff = (comp == np.argmax(st[1:, cv2.CC_STAT_AREA]) + 1).astype(np.uint8) * 255
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 128)
    under = cv2.dilate((ff != 128).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
    gray = ((lbl == 4) & (xs < 360)) | (under & (xs < 300) & (ys > 270))  # x ≥ 385 の灰色は棒なので外す
    light = ((lbl == 5) & (xs < 262)) | (under & (xs < 300) & (ys > 230) & (ys < 465))  # 水色の紙の下端は y≈465
    return smooth_trace(gray), smooth_trace(light)


def glyph_paths(font_path):
    """Nunito を WGHT で切り出し、doc と standards の字形を並べる。"""
    font = instantiateVariableFont(TTFont(font_path), {'wght': WGHT})
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font['hmtx']
    upm = font['head'].unitsPerEm
    scale = X_HEIGHT / font['OS/2'].sxHeight

    def word(text):
        names = [cmap[ord(ch)] for ch in text]
        adv = [hmtx[n][0] for n in names]
        return names, adv

    # doc と standards の間はラフの下線の幅ぶん空ける。下線は字形を使わず棒で描く
    d_names, d_adv = word('doc')
    s_names, s_adv = word('standards')
    under = 82 / scale  # ラフの下線の幅（px）を字の単位へ
    # 字間は書体のまま少しだけ広げる。ラフの全幅に合わせて詰めると doc が重なった
    track = TRACK
    out, boxes, x = [], [], 0.0
    for names, adv in ((d_names, d_adv), (s_names, s_adv)):
        for n, a in zip(names, adv):
            pen = SVGPathPen(gs)
            tx = TEXT_X0 + x * scale
            gs[n].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, BASELINE)))
            out.append(pen.getCommands())
            bp = BoundsPen(gs)
            gs[n].draw(bp)
            xmin, _, xmax, _ = bp.bounds
            boxes.append((n, tx + xmin * scale, tx + xmax * scale))  # 字の墨の左右（送り幅ではない）
            x += a + track
        if names is d_names:
            boxes.append(('underscore', TEXT_X0 + x * scale, TEXT_X0 + (x + under) * scale))
            x += under + track
    return out, boxes, scale, upm


def build(font_path):
    lbl = labels()
    gray_d, light_d = back_pages(lbl)
    glyphs, boxes, scale, _ = glyph_paths(font_path)

    cy = BASELINE - X_HEIGHT / 2  # 線は x の高さのまん中を通す
    bx = {n: (a, b) for n, a, b in boxes[:3]}
    d_l, d_r = bx[boxes[0][0]]
    o_l, o_r = bx[boxes[1][0]]
    c_l, c_r = bx[boxes[2][0]]
    u = next(b for b in boxes if b[0] == 'underscore')
    # 丸の位置: d の丸みの中心・d と o の間・o の中心・o と c の間・c の中心。ラフと同じ5つ
    d_bowl = d_l + (d_r - d_l) * 0.46  # d は右に縦棒があるので、丸みの中心は墨の幅のやや左
    stops = [d_bowl, (d_r + o_l) / 2, (o_l + o_r) / 2, (o_r + c_l) / 2, c_l + (c_r - c_l) * 0.52]
    rings = [  # (中心 x, 半径, 線幅, 色, 塗り)
        (stops[0], 15, 10, TEAL, WHITE),
        (stops[1], 14.5, 10, BLUE, WHITE),
        (stops[2], 24, 0, TEAL, TEAL),
        (stops[3], 14.5, 10, BLUE, WHITE),
        (stops[4], 15, 10, BLUE, WHITE),
    ]
    links = [(stops[0], stops[1], LIGHT), (stops[1], stops[2], LIGHT),
             (stops[2], stops[3], BLUE), (stops[3], stops[4], LIGHT)]

    def svg(text_color):
        defs = []
        # 文字は輪のまわりを抜く（白で縁取ると暗い地で白い輪が出るため）
        holes = ''.join(f'<circle cx="{x:.2f}" cy="{cy}" r="{r + w / 2 + GAP}" fill="#000"/>'
                        for x, r, w, *_ in rings)
        defs.append(f'<mask id="ds-text" maskUnits="userSpaceOnUse" x="0" y="0" width="4000" height="724"><rect x="0" y="0" width="4000" height="724" fill="#fff"/>{holes}</mask>')
        # 後ろの紙は前の紙のまわり（すき間ぶん広げた形）を抜く
        gap = 14
        defs.append(f'<mask id="ds-back" maskUnits="userSpaceOnUse" x="0" y="0" width="4000" height="724"><rect x="0" y="0" width="4000" height="724" fill="#fff"/>'
                    f'<path d="{page_outline(-gap)}" fill="#000"/></mask>')
        defs.append(f'<clipPath id="ds-page"><path d="{page_outline(STROKE / 2)}"/></clipPath>')
        body = [
            f'<g mask="url(#ds-back)"><path d="{gray_d}" fill="{GRAY}"/><path d="{light_d}" fill="{LIGHT}"/></g>',
            f'<path d="{page_outline(STROKE / 2)}" fill="{WHITE}"/>',
            # 折り返し: 斜辺と右上の角に沿う三角。紙の内側で切り、枠を上に重ねる
            f'<path clip-path="url(#ds-page)" d="M458 169L458 249A14 14 0 0 0 472 263L552 263Z" fill="{BLUE}"/>',
            f'<line x1="{NODE_X}" y1="{NODE_Y[0]}" x2="{NODE_X}" y2="{NODE_Y[2]}" stroke="{NAVY}" stroke-width="13"/>',
            ring(NODE_X, NODE_Y[0], RING_R, RING_W, NAVY).replace('fill="none"', f'fill="{WHITE}"'),
            f'<circle cx="{NODE_X}" cy="{NODE_Y[1]}" r="{DOT_R}" fill="{TEAL}"/>',
            ring(NODE_X, NODE_Y[2], RING_R, RING_W, NAVY).replace('fill="none"', f'fill="{WHITE}"'),
        ]
        for y, c in zip(NODE_Y, (GRAY, TEAL, GRAY)):
            body.append(f'<line x1="{BAR["x0"] + BAR["h"] / 2}" y1="{y}" x2="{BAR["x1"] - BAR["h"] / 2}" y2="{y}" '
                        f'stroke="{c}" stroke-width="{BAR["h"]}" stroke-linecap="round"/>')
        # 枠は外側の縁と内側の縁の差で塗る（線で描くと角の丸みが外と内で合わない）
        body.append(f'<path d="{page_outline(0)}{page_outline(STROKE)}" fill="{NAVY}" fill-rule="evenodd"/>')
        body.append(f'<g mask="url(#ds-text)" fill="{text_color}">' + ''.join(f'<path d="{g}"/>' for g in glyphs) + '</g>')
        uh = 26
        body.append(f'<rect x="{u[1]:.2f}" y="{BASELINE - 8}" width="{u[2] - u[1]:.2f}" height="{uh}" rx="{uh / 2}" fill="{TEAL}"/>')
        for a, b, c in links:
            body.append(f'<line x1="{a:.2f}" y1="{cy}" x2="{b:.2f}" y2="{cy}" stroke="{c}" stroke-width="11"/>')
        for x, r, w, c, f in rings:
            if w:
                body.append(f'<circle cx="{x:.2f}" cy="{cy}" r="{r}" fill="{f}" stroke="{c}" stroke-width="{w}"/>')
            else:
                body.append(f'<circle cx="{x:.2f}" cy="{cy}" r="{r}" fill="{c}"/>')
        # 余白 24px。左・上・下はラフの描かれた範囲から、右は文字の最後の墨から
        x0, y0, y1 = 117, 150, 560
        x1 = int(max(b[2] for b in boxes)) + 24
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}" '
                f'width="{x1 - x0}" height="{y1 - y0}" role="img" aria-label="doc_standards">'
                f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>')

    (LOGO / 'doc_standards.svg').write_text(svg(NAVY))
    (LOGO / 'doc_standards-dark.svg').write_text(svg(TEXT_DARK))
    print('書き出した:', LOGO / 'doc_standards.svg', LOGO / 'doc_standards-dark.svg')


if __name__ == '__main__':
    build(sys.argv[1])
