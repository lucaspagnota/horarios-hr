"""Draws the app icon (two beamed eighth notes on the ink background) at every size the site and the APK need."""
from pathlib import Path
from PIL import Image, ImageDraw

INK = (19, 23, 34, 255)
WHITE = (255, 255, 255, 255)
ROOT = Path(__file__).resolve().parent.parent


def glyph(draw, size, scale, ox, oy):
    # Same geometry as the in-app SVG mark (24x24 grid): stems + beam, two note heads.
    u = size * scale / 24
    X = lambda x: ox + x * u
    Y = lambda y: oy + y * u
    w = max(2, round(2.2 * u))
    draw.line([(X(9), Y(18)), (X(9), Y(5)), (X(21), Y(3)), (X(21), Y(16))], fill=WHITE, width=w, joint="curve")
    for cx, cy in ((6, 18), (18, 16)):
        r = 3.1 * u
        draw.ellipse([X(cx) - r, Y(cy) - r, X(cx) + r, Y(cy) + r], fill=WHITE)


def icon(size, scale=0.62, rounded=True, bg=INK, transparent=False):
    big = size * 4
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if not transparent:
        if rounded:
            d.rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 0.22, fill=bg)
        else:
            d.rectangle([0, 0, big, big], fill=bg)
    off = big * (1 - scale) / 2
    glyph(d, big, scale, off - big * scale * 0.01, off + big * scale * 0.02)
    return img.resize((size, size), Image.LANCZOS)


def main():
    web = ROOT / "web" / "icons"
    web.mkdir(parents=True, exist_ok=True)
    icon(192).save(web / "icon-192.png")
    icon(512).save(web / "icon-512.png")
    icon(512, scale=0.5, rounded=False).save(web / "icon-maskable-512.png")
    icon(180, rounded=False).save(web / "apple-touch-icon.png")
    icon(64).save(web / "favicon.png")
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    icon(1024, rounded=False).save(assets / "icon-only.png")
    icon(1024, scale=0.42, transparent=True).save(assets / "icon-foreground.png")
    Image.new("RGBA", (1024, 1024), INK).save(assets / "icon-background.png")
    for name, bg in (("splash.png", (244, 245, 249, 255)), ("splash-dark.png", (14, 16, 23, 255))):
        s = Image.new("RGBA", (2732, 2732), bg)
        mark = icon(420)
        s.alpha_composite(mark, ((2732 - 420) // 2, (2732 - 420) // 2))
        s.save(assets / name)


if __name__ == "__main__":
    main()
