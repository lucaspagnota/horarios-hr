"""Reads Lucas's lesson folder (HR-LUCAS) and builds the repertoire catalog the app imports.

    python3 scripts/repertorio.py "<path to HR-LUCAS>"

- Each instrument folder becomes one catalog entry; each subfolder becomes a section.
- A number at the start of a file name ("3-O Mar Serenou", "(MUSICA 1) Marcha", "13.1 Monte Castelo")
  is the teaching order. Files without a number are listed after the sequence.
- Word and text files are converted to PDF (LibreOffice) into "APP HORARIOS AULAS/Repertório/PDFs",
  mirroring the original folders. Originals are never touched, and files already converted are skipped.
- Writes "APP HORARIOS AULAS/Repertório/repertorio.json". In the app, Ajustes > Repertório reads it
  together with the files and sends them to Firebase Storage.
"""
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("APP HORARIOS AULAS") / "Repertório"
PDF_DIR = OUT_DIR / "PDFs"

# Top-level folder -> catalog entry. "instrumentos" matches the instrument written on each student.
INSTRUMENTOS = {
    "VIOLÃO E GUITAR": ("violao", "Violão e guitarra", ["Violão", "Guitarra"]),
    "VIOLINO": ("violino", "Violino", ["Violino"]),
    "BAIXO": ("baixo", "Contrabaixo", ["Baixo", "Contrabaixo"]),
    "CAVACO": ("cavaquinho", "Cavaquinho", ["Cavaquinho", "Cavaco"]),
    "VIOLA": ("viola", "Viola caipira", ["Viola caipira", "Viola"]),
    "UKULELE": ("ukulele", "Ukulele", ["Ukulele"]),
    "INFANTIL": ("infantil", "Infantil", []),
    "TEORIA MUSICAL": ("teoria", "Teoria musical", []),
    "CIFRAS": ("cifras", "Cifras (biblioteca)", []),
}
ORDEM = ["violao", "violino", "baixo", "cavaquinho", "viola", "ukulele", "infantil", "teoria", "cifras"]
# APOSTILAS/(CAVACO) xxx.pdf goes to that instrument's "Apostilas" section.
APOSTILA_TAG = {"CAVACO": "cavaquinho", "VIOLA": "viola", "VIOLINO": "violino", "VIOLÃO": "violao", "GUITARRA": "violao"}
# Loose files at the top of HR-LUCAS.
AVULSOS = {"Ebook-190-exercicios-guitarra.pdf": ("violao", "Apostilas")}

CONVERT = {".doc", ".docx", ".odt", ".rtf", ".txt"}
DIRECT = {".pdf": "pdf", ".png": "img", ".jpg": "img", ".jpeg": "img", ".gif": "img"}
SKIP_DIRS = {"AUDIOS", "MuseScore", ".mscbackup", "APP HORARIOS AULAS"}

# "3-Título", "(MUSICA 1) Título", "1. Título", "13.1 Título". A bare "11 Vidas" is a title, not an order.
NUM_RE = re.compile(r"^\s*(?:\(\s*(?:m[uú]sica\s*)?(\d{1,3})\s*\)|(\d{1,3})\s*[-–.](?!\d)|(\d{1,3}\.\d{1,2})\s)\s*", re.I)
# The chord library has no teaching order (hymn numbers like "107 Creio..." are part of the title).
SEM_ORDEM = {"cifras"}
TOM_RE = re.compile(r"(?:\s+-\s*|\s*\(\s*|\s+)([A-G](?:#|b)?m?)\s*\)?$")


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def pretty(s):
    s = re.sub(r"\s+", " ", s.replace("_", " ")).strip(" -")
    if s.isupper() and len(s) > 3:
        small = {"de", "da", "do", "das", "dos", "e", "o", "a", "os", "as", "em", "no", "na", "of", "the"}
        words = s.lower().split()
        s = " ".join(w if i and w in small else w[:1].upper() + w[1:] for i, w in enumerate(words))
    return {"Musicas": "Músicas"}.get(s, s)


def parse_name(stem, ordem=True):
    n = None
    m = NUM_RE.match(stem) if ordem else None
    if m:
        n = float(next(g for g in m.groups() if g))
        stem = stem[m.end():]
    tom = ""
    m = TOM_RE.search(stem)
    if m and len(stem) > m.end() - m.start() + 2:
        tom, stem = m.group(1), stem[: m.start()]
    return n, pretty(stem), tom


def sha(path):
    h = hashlib.sha1()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def wanted(path):
    if path.name.startswith("~$") or path.name.startswith("."):
        return False
    return path.suffix.lower() in CONVERT or path.suffix.lower() in DIRECT


def dedupe(files):
    """Same name in the same folder: PDF beats Word, .docx beats .doc."""
    rank = {".pdf": 0, ".docx": 1, ".doc": 2}
    best = {}
    for f in files:
        stem = f.stem[:-5] if f.stem.lower().endswith(".docx") else f.stem
        key = (f.parent, norm(stem))
        r = rank.get(f.suffix.lower(), 3) + (5 if f.stem.lower().endswith(".docx") else 0)
        if key not in best or r < best[key][0]:
            best[key] = (r, f)
    return sorted(f for _, f in best.values())


def convert(root, files):
    """Converts Word/text files to PDF under PDF_DIR, one LibreOffice call per folder."""
    todo = {}
    for f in files:
        if f.suffix.lower() in CONVERT:
            out = root / PDF_DIR / f.relative_to(root).with_suffix(".pdf")
            if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
                todo.setdefault(out.parent, []).append(f)
    total = sum(len(v) for v in todo.values())
    done = 0
    for outdir, batch in todo.items():
        outdir.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(batch), 40):
            chunk = batch[i : i + 40]
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), *map(str, chunk)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
            done += len(chunk)
            print(f"convertidos {done}/{total}", flush=True)


def main():
    root = Path(sys.argv[1]).resolve()
    files = []
    for top in sorted(p for p in root.iterdir()):
        if top.is_file():
            if top.name in AVULSOS or wanted(top):
                files.append(top)
            continue
        if top.name in SKIP_DIRS:
            continue
        for f in top.rglob("*"):
            if f.is_file() and wanted(f) and not (set(f.relative_to(root).parts[:-1]) & SKIP_DIRS):
                files.append(f)
    files = dedupe(files)
    if "--sem-converter" not in sys.argv:
        convert(root, files)

    cat = {}
    for key, (iid, nome, instr) in INSTRUMENTOS.items():
        cat[iid] = {"id": iid, "nome": nome, "instrumentos": instr, "secoes": {}}
    sem_pdf = []
    for f in files:
        rel = f.relative_to(root)
        parts = rel.parts
        ordem = not (len(parts) == 1 or INSTRUMENTOS.get(parts[0], ("",))[0] in SEM_ORDEM)
        n, titulo, tom = parse_name(f.stem[:-5] if f.stem.lower().endswith(".docx") else f.stem, ordem)
        if len(parts) == 1:
            iid, sec = AVULSOS.get(f.name, ("cifras", "Avulsas"))
        elif parts[0] == "APOSTILAS":
            m = re.match(r"\((.+?)\)\s*(.*)", f.stem)
            iid = APOSTILA_TAG.get(m.group(1).upper(), "teoria") if m else "teoria"
            titulo = pretty(m.group(2)) if m else titulo
            sec = "Apostilas"
        elif parts[0] in INSTRUMENTOS:
            iid = INSTRUMENTOS[parts[0]][0]
            sec = " / ".join(pretty(p) for p in parts[1:-1]) or "Principal"
        else:
            continue
        if f.suffix.lower() in CONVERT:
            src = PDF_DIR / rel.with_suffix(".pdf")
            if not (root / src).exists():
                sem_pdf.append(str(rel))
                continue
            tipo = "pdf"
        else:
            src, tipo = rel, DIRECT[f.suffix.lower()]
        ext = ".pdf" if tipo == "pdf" else f.suffix.lower()
        item = {
            "id": hashlib.sha1(f"{iid}|{sec}|{norm(titulo)}|{tom}".encode()).hexdigest()[:10],
            "n": n, "t": titulo, "tom": tom, "tipo": tipo,
            "f": f"rep/{sha(f)}{ext}",
            "src": Path(src).as_posix(),
            "orig": rel.as_posix(),
        }
        cat[iid]["secoes"].setdefault(sec, []).append(item)

    out = []
    for iid in ORDEM:
        c = cat[iid]
        secoes = []
        for sec, itens in c["secoes"].items():
            seen, uniq = set(), []
            for it in sorted(itens, key=lambda x: (x["n"] is None, x["n"] or 0, norm(x["t"]))):
                if it["id"] in seen:
                    it["id"] += "-" + it["f"][4:8]
                seen.add(it["id"])
                uniq.append(it)
            secoes.append({"id": hashlib.sha1(f"{iid}|{sec}".encode()).hexdigest()[:8], "nome": sec,
                           "sequencia": any(i["n"] is not None for i in uniq), "itens": uniq})
        # Sections with a numbered sequence first, then the rest by name.
        secoes.sort(key=lambda s: (not s["sequencia"], s["nome"] != "Principal", norm(s["nome"])))
        c["secoes"] = secoes
        out.append(c)

    manifest = {"versao": 1, "gerado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "catalogo": out}
    (root / OUT_DIR).mkdir(parents=True, exist_ok=True)
    (root / OUT_DIR / "repertorio.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(s["itens"]) for c in out for s in c["secoes"])
    print(f"{total} arquivos no catálogo; {len(sem_pdf)} sem PDF")
    for s in sem_pdf[:30]:
        print("  sem PDF:", s)


if __name__ == "__main__":
    main()
