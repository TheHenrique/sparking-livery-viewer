"""Gera a faixa do para-brisa (material WCEXTRA1): fundo preto, nome em branco.
O texto fica centralizado na altura onde estava o texto do banner original."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'Poppins-Bold.ttf')

def text_band(orig):
    """(y0, y1) da faixa onde esta o texto no banner original."""
    g = np.asarray(orig.convert('L'), dtype=float)
    dx = np.abs(np.diff(g, axis=1)) > 40
    score = dx.sum(1).astype(float)
    if score.max() == 0: return 0, orig.height
    rows = np.where(score > 0.35 * score.max())[0]
    # maior grupo de linhas proximas (tolera buracos de ate 4 px entre letras)
    groups, cur = [], [rows[0]]
    for r in rows[1:]:
        if r - cur[-1] <= 4: cur.append(r)
        else: groups.append(cur); cur = [r]
    groups.append(cur)
    best = max(groups, key=lambda g: (len(g), -g[0]))
    return int(best[0]), int(best[-1]) + 1

def make(orig, text):
    w, h = orig.size
    y0, y1 = text_band(orig)
    cy = (y0 + y1) / 2
    target_h = min(0.075 * w, 0.55 * h)      # altura do texto proporcional a largura da faixa (igual em todos)
    img = Image.new('RGB', (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    # maior fonte que caiba em 72% da largura e na altura alvo
    size = 8
    while True:
        f = ImageFont.truetype(FONT, size + 1)
        l, t, r, b = d.textbbox((0, 0), text, font=f)
        if r - l > w * 0.72 or b - t > target_h: break
        size += 1
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text(((w - (r - l)) / 2 - l, cy - (b - t) / 2 - t), text, font=f, fill=(255, 255, 255))
    return img
