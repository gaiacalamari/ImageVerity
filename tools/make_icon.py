"""Disegna l'icona del programma (monogramma «IV» su quadrato scuro) in src/fvp/ui/assets/fvp.ico.

Uso: python tools/make_icon.py
Serve solo Pillow. Le lettere sono disegnate come forme geometriche, senza caratteri installati: l'icona è
identica su ogni computer, riproducibile e modificabile senza programmi di grafica. Si disegna a 1024 px e si
riduce a 16-256 px; la sottolineatura verde richiama la verifica.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "src" / "fvp" / "ui" / "assets" / "fvp.ico"
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

S = 1024
INK = (24, 24, 27, 255)        # quasi nero, come il pulsante principale dell'interfaccia
PAPER = (250, 250, 249, 255)   # quasi bianco
ACCENT = (46, 158, 91, 255)    # verde "verificato"


def draw(size: int = S) -> Image.Image:
    k = size / S
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m, r = 32 * k, 72 * k                                   # margine trasparente, angoli appena smussati
    d.rounded_rectangle([m, m, size - m, size - m], radius=r, fill=INK)

    h, s = 500 * k, 150 * k                                 # altezza lettere, spessore del tratto
    w_i, gap, w_v = s, 90 * k, 470 * k
    x0 = (size - (w_i + gap + w_v)) / 2
    y0, y1 = 210 * k, 210 * k + h
    d.rectangle([x0, y0, x0 + w_i, y1], fill=PAPER)        # I
    xv = x0 + w_i + gap                                     # V: due tratti che si uniscono in basso
    cx = xv + w_v / 2
    d.polygon([(xv, y0), (xv + s, y0), (cx + s / 2, y1), (cx - s / 2, y1)], fill=PAPER)
    d.polygon([(xv + w_v - s, y0), (xv + w_v, y0), (cx + s / 2, y1), (cx - s / 2, y1)], fill=PAPER)
    by = y1 + 64 * k                                        # sottolineatura
    d.rectangle([x0, by, xv + w_v, by + 48 * k], fill=ACCENT)
    return img


if __name__ == "__main__":
    big = draw(S)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    big.resize((256, 256), Image.LANCZOS).save(OUT, sizes=SIZES)
    print(f"Icona scritta in {OUT}")
