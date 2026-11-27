"""Link havuzundan 2.0.0'ın catalog-update.json dosyasını ÜRET (canlı kanal için).

Kurallar (eboot'taki catalog-update.js'ten okundu):
  - format: 1, version: "2.0.0" (uygulamanın VERSION'ı), generated, games[], removed[]
  - releases: { "<TID>": [ {id, filename, format, url, ...} ] }, pages: {}
  - <= 4 MB
Bu dosya `catalog` dalına yazılır; Action saatte bir yeniler.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = os.path.join(HERE, "links")
OUT = os.path.join(HERE, "public", "catalog-update.json")
APP_VERSION = "2.0.0"
MAX_BYTES = 4 * 1024 * 1024
PROVIDER_FORMAT = {}


def load(tid):
    with open(os.path.join(LINKS, tid + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


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


def build() -> dict:
    releases = {}
    for name in sorted(os.listdir(LINKS)) if os.path.isdir(LINKS) else []:
        if not name.endswith(".json"):
            continue
        tid = name[:-5]
        if not re.fullmatch(r"[A-Z]{4}\d{5}", tid):
            continue
        meta = load(tid)
        rows = [release_of(tid, e, meta) for e in meta.get("links", [])]
        if rows:
            releases[tid] = rows
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
    return {"bytes": len(payload), "tids": list(releases), "path": OUT}


if __name__ == "__main__":
    print(json.dumps(build(), indent=1, ensure_ascii=False))
