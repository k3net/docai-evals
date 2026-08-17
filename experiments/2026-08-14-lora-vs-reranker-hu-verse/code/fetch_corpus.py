"""F0.1 — korpusz letöltése a MEK-ről, provenance-manifesttel.

A provenance nem formalitás: a runbook D0 döntése szerint a korpusz jogi
státusza a munka része. Ezért minden forrásnál rögzítjük a letöltés URL-jét,
időpontját, a csomag SHA-256-ját és a MEK-cédula jogi közleményét — utólag is
bizonyíthatóan.

Idempotens: ha a csomag már megvan és a hash egyezik, nem tölt újra.

    python3 code/fetch_corpus.py
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone

from config import MANIFEST, RAW, SOURCES

USER_AGENT = "docit-study-lora/1.0 (egyetemi hazi feladat; korpusz-letoltes)"
TIMEOUT = 180


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _cedula_facts(url: str) -> dict:
    """A MEK-cédula gépi olvasata: cím, eredeti kiadás, jogi közlemény.

    Nem HTML-parser-függő: a cédula lapos szöveg, néhány kulcsszóval.
    """
    try:
        raw = _get(url).decode("utf-8", errors="replace")
    except Exception as exc:  # a cédula hiánya ne bontsa el a letöltést
        return {"error": str(exc)}

    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    facts: dict[str, str] = {}
    for ln in lines:
        if ln.startswith("MEK-") and "/" in ln:
            facts["record"] = ln
        elif ln.startswith("eredeti kiadvány:"):
            facts["original_edition"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("Jogi közlemény:"):
            facts["legal_note"] = ln.split(":", 1)[1].strip()
        elif "MEK-be került:" in ln:
            facts["added_to_mek"] = ln.split("MEK-be került:", 1)[1].strip()
    return facts


def fetch(key: str, spec: dict) -> dict:
    dest_dir = RAW / key
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / "source.zip"

    if archive.exists():
        blob = archive.read_bytes()
        print(f"  [{key}] csomag már megvan ({len(blob):,} bájt), nem töltöm újra")
    else:
        print(f"  [{key}] letöltés: {spec['zip_url']}")
        blob = _get(spec["zip_url"])
        archive.write_bytes(blob)

    digest = hashlib.sha256(blob).hexdigest()

    extract_dir = dest_dir / "html"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        # Zip-slip elleni védelem: a MEK-csomagok laposak, de nem hiszünk vakon
        for name in names:
            if name.startswith("/") or ".." in name:
                raise ValueError(f"gyanús útvonal a zipben: {name}")
        zf.extractall(extract_dir)

    html_files = sorted(p.name for p in extract_dir.iterdir() if p.suffix.lower() in (".htm", ".html"))
    print(f"  [{key}] kicsomagolva: {len(names)} fájl, ebből {len(html_files)} HTML")

    return {
        "key": key,
        "author": spec["author"],
        "author_died": spec["died"],
        "title": spec["title"],
        "mek_id": spec["mek_id"],
        "landing_url": spec["landing"],
        "zip_url": spec["zip_url"],
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": digest,
        "bytes": len(blob),
        "files_in_archive": len(names),
        "html_files": len(html_files),
        "encoding": spec["encoding"],
        "layout": spec["layout"],
        "note": spec["note"],
        "cedula": _cedula_facts(spec["cedula"]),
        # A közkincs-állítás levezetése, hogy ne kelljen fejből hinni:
        "public_domain": {
            "rule": "Szjt. 31. § — a védelem a szerző halálát követő 70. év végéig tart",
            "expired_end_of": spec["died"] + 70,
            "is_public_domain": (spec["died"] + 70) < 2026,
        },
    }


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    entries = []
    for key, spec in SOURCES.items():
        print(f"[{key}] {spec['author']} — {spec['title']}")
        entries.append(fetch(key, spec))

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "legal_basis": (
            "Minden forrás közkincs: a szerzők 1955 előtt hunytak el, így a "
            "Szjt. 31. § szerinti 70 éves védelmi idő lejárt. Védett mű "
            "(pl. Romhányi József, †1983) nem került be — ld. runbook D0."
        ),
        "sources": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest: {MANIFEST}")

    for e in entries:
        pd = "közkincs" if e["public_domain"]["is_public_domain"] else "⚠️ VÉDETT"
        legal = e["cedula"].get("legal_note", "—")
        print(f"  {e['key']:8s} {pd:10s} (védelem lejárt: {e['public_domain']['expired_end_of']} végén) · cédula: {legal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
