"""Link Havuzu — yayın adımı: doğrulama raporundan uygulamanın okuyacağı JSON'u üretir.

Girdi : verify-report.json
Çıktı : public/links/index.json          (tüm TID'ler ve özet)
        public/links/<TID>.json          (yalnız geçerli linkler, öncelik sırasıyla)
Kural : ölü linkler silinmez (dead_at ile işaretli gelir), uygulama sırasıyla dener.
"""
from __future__ import annotations

import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "verify-report.json")
LINKS = os.path.join(HERE, "links")
PUB = os.path.join(HERE, "public", "links")


def load_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def main() -> dict:
    report = load_json(REPORT, {})
    os.makedirs(PUB, exist_ok=True)
    index = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "games": []}
    published = 0

    for tid in sorted(report):
        rep = report[tid]
        src = load_json(os.path.join(LINKS, tid + ".json"), {})
        verified = {row["provider"]: row for row in rep.get("links", [])}
        out_links = []
        for entry in src.get("links", []):
            row = verified.get(entry.get("provider"), {})
            out = {
                "provider": entry.get("provider"),
                "url": entry.get("url"),
                "bytes": entry.get("verified_bytes") or row.get("bytes"),
                "expires": entry.get("expires"),
                "ok": bool(row.get("ok")),
                "checked_at": row.get("checked_at"),
            }
            if not row.get("ok"):
                out["dead_at"] = row.get("checked_at") or time.time()
                out["dead_reason"] = row.get("reason") or "verify failed"
            out_links.append(out)
        out_links.sort(key=lambda x: (not x["ok"], x.get("expires") or 0))
        payload = {
            "titleId": tid,
            "title": src.get("title") or rep.get("title"),
            "bytes": src.get("bytes"),
            "generated": index["generated"],
            "links": out_links,
        }
        with open(os.path.join(PUB, tid + ".json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        index["games"].append({"titleId": tid, "title": payload["title"],
                               "valid": sum(1 for x in out_links if x["ok"]),
                               "total": len(out_links)})
        published += 1

    with open(os.path.join(PUB, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    return {"published": published, "index": os.path.join(PUB, "index.json")}


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, ensure_ascii=False))
