"""Builds the standalone site (GitHub Pages + APK) into www/ from app/horarios-hr.html.

The same app/horarios-hr.html is published as-is inside Claude. Here it gets a real <head>,
the PWA manifest and service worker, and the Firebase settings when firebase.config.json exists.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / "www"
FIREBASE_FILES = ["firebase-app-compat.js", "firebase-auth-compat.js", "firebase-firestore-compat.js", "firebase-storage-compat.js"]


def main():
    src = (ROOT / "app" / "horarios-hr.html").read_text(encoding="utf-8")
    # Everything before the app shell (title, metas, font links, <style>) belongs in <head>.
    split = src.index('<div class="shell">')
    head_part, body_part = src[:split], src[split:]

    if WWW.exists():
        shutil.rmtree(WWW)
    (WWW / "vendor").mkdir(parents=True)
    shutil.copytree(ROOT / "web" / "icons", WWW / "icons")
    shutil.copy(ROOT / "web" / "manifest.webmanifest", WWW / "manifest.webmanifest")

    cfg_path = ROOT / "firebase.config.json"
    firebase = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else None
    vendor_tags = ""
    if firebase:
        nm = ROOT / "node_modules" / "firebase"
        for f in FIREBASE_FILES:
            shutil.copy(nm / f, WWW / "vendor" / f)
        vendor_tags = "\n".join(f'<script src="vendor/{f}"></script>' for f in FIREBASE_FILES)

    flags = "window.HR_STANDALONE = true;"
    if firebase:
        flags += f"\nwindow.HR_FIREBASE = {json.dumps(firebase)};"

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icons/favicon.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<script>{flags}
window.addEventListener('beforeinstallprompt', e => {{ e.preventDefault(); window.HR_INSTALL = e; }});</script>
{vendor_tags}
{head_part.strip()}
</head>
<body>
{body_part.strip()}
<script>
if ('serviceWorker' in navigator && location.protocol === 'https:' && !window.Capacitor) {{
  navigator.serviceWorker.register('sw.js').catch(() => {{}});
}}
</script>
</body>
</html>
"""
    (WWW / "index.html").write_text(html, encoding="utf-8")

    # Service worker cache name changes whenever any published file changes (page, icons, manifest,
    # Firebase scripts) so phones pick up new versions.
    digest = hashlib.sha1()
    for f in sorted(p for p in WWW.rglob("*") if p.is_file()):
        digest.update(f.relative_to(WWW).as_posix().encode("utf-8"))
        digest.update(f.read_bytes())
    version = digest.hexdigest()[:10]
    sw = (ROOT / "web" / "sw.js").read_text(encoding="utf-8").replace("__VERSION__", version)
    (WWW / "sw.js").write_text(sw, encoding="utf-8")
    print(f"www/ pronto (versão {version}, Firebase {'ligado' if firebase else 'desligado'})")


if __name__ == "__main__":
    main()
