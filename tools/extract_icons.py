#!/usr/bin/env python3
"""
Extrai ícones de uma "folha de ícones" (grade com legenda) gerada na Adapta
e salva cada um como PNG transparente em assets/icons/<slug>.png.

Uso:
  python tools/extract_icons.py tools/sheets/parte2.json
  python tools/extract_icons.py tools/sheets/parte2.json --out /tmp/teste --debug

O JSON de configuração descreve a folha (veja tools/sheets/*.json):
  image     caminho da imagem (864x1536)
  grid_top  y do topo da 1ª linha de ícones (ver "Calibração" no CLAUDE.md)
  row_h     altura de cada linha da grade
  x0, x1    limites horizontais do interior branco do cartão
  rows      lista de linhas; cada linha é a lista de nomes dos pratos, em ordem

Método (importante — o método ingênuo de "caixa fixa" CORTOU bordas de ícones):
  1. para cada célula, abre uma janela GENEROSA ao redor do centro estimado
  2. máscara = pixels saturados OU contorno escuro (valor < 0.35)
  3. dilata, rotula componentes conexos, fica com o MAIOR
  4. recorta no bbox desse componente + margem
  5. branco (soma RGB > 245*3) vira transparente
"""
import argparse, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage


def slugify(s: str) -> str:
    s = s.lower().strip()
    for pat, rep in [(r'[áàâã]', 'a'), (r'[éê]', 'e'), (r'[íî]', 'i'),
                     (r'[óôõ]', 'o'), (r'[úû]', 'u'), (r'ç', 'c')]:
        s = re.sub(pat, rep, s)
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def find_icon_crop(im, cx, cy, win_w, win_h, sat_thresh=0.08, dilate=4, pad=6):
    W, H = im.size
    x0, x1 = max(0, int(cx - win_w / 2)), min(W, int(cx + win_w / 2))
    y0, y1 = max(0, int(cy - win_h / 2)), min(H, int(cy + win_h / 2))
    region = im.crop((x0, y0, x1, y1))
    arr = np.array(region).astype(float) / 255.0
    maxc, minc = arr.max(axis=2), arr.min(axis=2)
    sat = np.where(maxc > 0, (maxc - minc) / np.where(maxc == 0, 1, maxc), 0)
    mask = ((sat > sat_thresh) | (maxc < 0.35)) & (maxc > 0.03)
    mask = ndimage.binary_dilation(mask, iterations=dilate)
    labeled, num = ndimage.label(mask)
    if num == 0:
        return region
    sizes = ndimage.sum(mask, labeled, range(1, num + 1))
    ys, xs = np.where(labeled == (np.argmax(sizes) + 1))
    return region.crop((max(0, xs.min() - pad), max(0, ys.min() - pad),
                        min(region.width, xs.max() + pad), min(region.height, ys.max() + pad)))


def make_transparent(im, thresh=245):
    arr = np.array(im.convert("RGBA"))
    arr[:, :, 3] = np.where(arr[:, :, :3].astype(int).sum(axis=2) > thresh * 3, 0, 255)
    return Image.fromarray(arr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--out", default="assets/icons")
    ap.add_argument("--debug", action="store_true", help="salva também um contact sheet em fundo escuro")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.config))
    img_path = cfg["image"] if os.path.isabs(cfg["image"]) else os.path.normpath(os.path.join(base, cfg["image"]))
    im = Image.open(img_path).convert("RGB")
    os.makedirs(a.out, exist_ok=True)

    results = {}
    for r, row in enumerate(cfg["rows"]):
        # IMPORTANTE: cada linha é espaçada pela QUANTIDADE DE ITENS DAQUELA LINHA
        # (linhas incompletas se redistribuem na largura toda — não reusam a grade das cheias)
        col_w = (cfg["x1"] - cfg["x0"]) / len(row)
        cy = cfg["grid_top"] + cfg["row_h"] * (r + 0.5)
        for c, name in enumerate(row):
            cx = cfg["x0"] + col_w * (c + 0.5)
            crop = find_icon_crop(im, cx, cy, col_w * 1.5, cfg["row_h"] * 1.35)
            results[name] = make_transparent(crop)

    for name, icon in results.items():
        icon.save(os.path.join(a.out, slugify(name) + ".png"))
    print(f"{len(results)} ícones salvos em {a.out}")

    if a.debug:
        from PIL import ImageDraw
        names = list(results)
        cols, th = 6, 180
        rows = (len(names) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * th, rows * th), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for i, n in enumerate(names):
            t = results[n].copy(); t.thumbnail((th - 14, th - 36))
            x, y = (i % cols) * th, (i // cols) * th
            d.rectangle([x + 3, y + 3, x + th - 3, y + th - 3], outline=(255, 0, 0))
            sheet.paste(t, (x + 7, y + 7), t)
            d.text((x + 4, y + th - 28), n[:24], fill="white")
        p = os.path.join(a.out, "_debug_contact_sheet.png")
        sheet.save(p); print("debug:", p)


if __name__ == "__main__":
    sys.exit(main())
