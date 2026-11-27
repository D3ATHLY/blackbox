"""Link havuzundan 2.0.0'nin catalog-update.json dosyasini URET (canli kanal icin).

Kurallar (eboot'taki catalog-update.js'ten okundu):
  - format: 1, version: "2.0.0", generated, games[], removed[]
  - releases: { "<TID>": [ {id, filename, format, url, ...} ] }, pages: {}
  - <= 4 MB
Bu dosya `catalog` dalina yazilir; Action saatte bir yeniler.

Onemli:
  * Sadece `verify-report.json` icinde ok=True olan havuz linkleri yayinlanir.
  * `linkpool/base/<TID>.json` varsa (imajdaki gomulu kaynaklar) onlar da listeye
    eklenir; boylece token suresi dolsa bile oyun kaynakssiz kalmaz.
  * Hicbir gecerli kaynak yoksa o TID yayinlanmaz (uygulama kendi gomulu verisini korur).
"""
from __future__ import annotations

import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = os.path.join(HERE, "links")
BASE = os.path.join(HERE, "base")
REPORT = os.path.join(HERE, "verify-report.json")
OUT = os.path.join(HERE, "public", "catalog-update.json")
APP_VERSION = "2.0.0"
MAX_BYTES = 4 * 1024 * 1024


def load(path, fallback=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def release_of(tid: str, entry: dict, meta: dict) -> dict:
    return {
        "id": "pool-" + tid.lower() + "-" + str(entry["provider"]),
        "format": "pkg",
        "filename": meta.get("filename") or (tid + ".pkg"),
        "url": entry["url"],
        "browserUrl": entry["url"],
        "requiresBrowser": False,
        "sizeBytes": entry.get("verified_bytes"),
        "version": meta.get("version") or "",
        "category": "game",
        "provider": entry["provider"],
        "source": "pool",
        "flow": "direct",
        "label": entry["provider"],
        "role": "base",
        "expires": entry.get("expires"),
    }


def verified_ok(report: dict) -> dict:
    """{tid: set(provider)} - yalnizca dogrulamadan gecen saglayicilar."""
    out = {}
    for tid, rep in (report or {}).items():
        ok = {row.get("provider") for row in rep.get("links", []) if row.get("ok")}
        out[tid] = ok
    return out


def build() -> dict:
    report = load(REPORT, {})
    ok_map = verified_ok(report)
    releases = {}
    skipped = {}
    names = sorted(os.listdir(LINKS)) if os.path.isdir(LINKS) else []
    for name in names:
        if not name.endswith(".json"):
            continue
        tid = name[:-5]
        if not re.fullmatch(r"[A-Z]{4}\d{5}", tid):
            continue
        meta = load(os.path.join(LINKS, name), {})
        ok = ok_map.get(tid, set())
        rows = [release_of(tid, e, meta) for e in meta.get("links", [])
                if e.get("provider") in ok]
        # gomulu (imajdaki) kaynaklar: her zaman yedek olarak eklensin
        live_keys = {str(e.get("provider") or "").lower() for e in meta.get("links", [])
                     if e.get("provider") in ok}
        for row in load(os.path.join(BASE, name), []) or []:
            if not isinstance(row, dict) or not row.get("url"):
                continue
            base_key = str(row.get("provider") or "").lower()
            # ayni saglayicinin havuzdaki dogrudan linki varken sayfayi tekrar gosterme
            if any(k and (base_key.startswith(k) or k.startswith(base_key)) for k in live_keys):
                continue
            rows.append(dict(row))
        # ayni URL iki kez gitmesin
        seen = set()
        uniq = []
        for row in rows:
            url = str(row.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            uniq.append(row)
        if uniq:
            releases[tid] = uniq
        else:
            skipped[tid] = "gecerli kaynak yok"

    update = {
        "format": 1,
        "version": APP_VERSION,
        "base": "pool",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "games": [],
        "removed": [],
        "releases": releases,
        "pages": {},
    }
    payload = json.dumps(update, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise SystemExit("4 MB sinirini asiyor")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as fh:
        fh.write(payload)
    return {"bytes": len(payload), "tids": {k: len(v) for k, v in releases.items()},
            "skipped": skipped, "path": OUT}


if __name__ == "__main__":
    print(json.dumps(build(), indent=1, ensure_ascii=False))
