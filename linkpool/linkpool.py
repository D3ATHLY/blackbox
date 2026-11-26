"""Link Havuzu — 1. adım: şema + doğrulayıcı (yalnız ölçer, hiçbir şeyi değiştirmez).

Kullanım:
  python linkpool.py notes     -> NOTLAR.md üretir
  python linkpool.py verify    -> links/<TID>.json içindeki tüm linkleri sınar
  python linkpool.py verify --tid PPSA38500
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = os.path.join(HERE, "links")
PKG_MAGIC = bytes.fromhex("7f464948")  # \x7fFIH -> PS5 PKG başlığı
UA = "BlackBox-LinkPool/1.0 (+verify only)"

# Sağlayıcı profilleri: yeni sağlayıcı eklemek = buraya bir satır yazmak.
PROVIDERS = {
    "mocha": {
        "label": "MochaProxy",
        "ttl_hours": 24,
        "signature_hint": ["token=", "expires="],
        "note": "token+expires URL imzası; IP bağlı değil (ölçüldü)",
    },
    "viking": {
        "label": "Vikingfile (S3 R2)",
        "ttl_hours": 48,
        "signature_hint": ["X-Amz-Signature", "X-Amz-Expires"],
        "note": "AWS SigV4; imza URL'ye ait, farklı cihazdan çalışıyor (ölçüldü)",
    },
    # yeni sağlayıcı örneği:
    # "datanodes": {"label": "DataNodes", "ttl_hours": 24, "signature_hint": ["token="], "note": ""},
}


def load(tid: str) -> dict:
    with open(os.path.join(LINKS, tid + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def all_tids() -> list[str]:
    if not os.path.isdir(LINKS):
        return []
    return sorted(n[:-5] for n in os.listdir(LINKS) if n.endswith(".json"))


def verify_url(url: str, expect_bytes: int | None = None) -> dict:
    """HEAD yoksa Range 0-1023 ile ölç; PKG imzasını ve boyutu kontrol et."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-1023"})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            head = r.read(1024)
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            status = r.status
    except urllib.error.HTTPError as exc:
        return {"ok": False, "reason": f"HTTP {exc.code}", "checked_at": time.time()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)[:160], "checked_at": time.time()}

    total = None
    rng = hdrs.get("content-range", "")
    m = re.search(r"/(\d+)$", rng)
    if m:
        total = int(m.group(1))
    magic_ok = head[:4] == PKG_MAGIC
    size_ok = expect_bytes is None or total == expect_bytes
    return {
        "ok": status in (200, 206) and magic_ok and size_ok,
        "http": status,
        "bytes": total,
        "pkg_magic": magic_ok,
        "size_ok": size_ok,
        "server": hdrs.get("server"),
        "filename": (hdrs.get("content-disposition") or "")[:160],
        "ms": round((time.time() - started) * 1000),
        "checked_at": time.time(),
    }


def verify(tid: str | None = None) -> dict:
    tids = [tid] if tid else all_tids()
    report = {}
    for t in tids:
        data = load(t)
        rows = []
        for entry in data.get("links", []):
            res = verify_url(entry["url"], entry.get("bytes"))
            unknown = entry.get("provider") not in PROVIDERS
            res["provider"] = entry.get("provider")
            res["unknown_provider"] = unknown
            rows.append({"provider": entry.get("provider"), **res})
        report[t] = {
            "title": data.get("title"),
            "titleId": data.get("titleId"),
            "links": rows,
            "ok_count": sum(1 for r in rows if r["ok"]),
            "fail_count": sum(1 for r in rows if not r["ok"]),
        }
    return report


def notes() -> str:
    lines = ["# Link Havuzu — NOTLAR", "",
             f"> Güncelleme: {time.strftime('%Y-%m-%d %H:%M')}", "",
             "## Nasıl çalışır",
             "1. Bir gönüllü PS5'te browser'ı açar, Cloudflare'i geçer, **doğrudan** dosya linkini alır.",
             "2. Linki `links/<TID>.json` içine `provider` etiketiyle ekler (PR ya da doğrudan commit).",
             "3. `python linkpool.py verify` tüm linkleri sınar: HTTP 200/206 + PKG imzası + boyut.",
             "4. Yalnız `ok: true` olanlar uygulamaya servis edilir (Pages/Worker).",
             "", "## Doğrulanmış sağlayıcılar", "",
             "| Sağlayıcı | Etiket | Ömür | İmza | Not |", "|---|---|---|---|---|"]
    for key, p in PROVIDERS.items():
        lines.append(f"| `{key}` | {p['label']} | {p['ttl_hours']} saat | "
                     f"`{', '.join(p['signature_hint'])}` | {p['note']} |")
    lines += ["", "## Yeni sağlayıcı eklemek",
              "- Mantık aynıysa (URL'ye gömülü imza, IP bağlı değil) `PROVIDERS` sözlüğüne bir satır ekle.",
              "- Sonra `links/<TID>.json` içinde `provider` alanında bu anahtarı kullan.",
              "- Değişiklik bu dosyada; hiçbir imaj/kod değişmez.",
              "", "## GTA VI (PPSA38500) — test kaydı", "",
              "- `mocha`: 216.513.692.961 byte, `7f 46 49 48` imzası doğrulandı, ~24 saat",
              "- `viking`: 221.028.009.318 byte, aynı imza, ~48 saat",
              "- Ölçüm: PC + PS5 + mobil veri, farklı IP → **ikisi de indirilebiliyor**",
              "", "## Kural", "- Link ölürse silinmez, `dead_at` yazılır; uygulama sıradaki sağlıklıya düşer.",
              "- Havuzdaki linkler herkese açıktır; telif sorumluluğu linki ekleyendedir."]
    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "notes"
    if cmd == "notes":
        path = os.path.join(HERE, "NOTLAR.md")
        open(path, "w", encoding="utf-8").write(notes())
        print(path)
    elif cmd == "verify":
        tid = None
        if "--tid" in sys.argv:
            tid = sys.argv[sys.argv.index("--tid") + 1]
        out = verify(tid)
        open(os.path.join(HERE, "verify-report.json"), "w", encoding="utf-8").write(
            json.dumps(out, indent=1, ensure_ascii=False))
        print(json.dumps({k: {"ok": v["ok_count"], "fail": v["fail_count"]} for k, v in out.items()}, indent=1))
    else:
        print(__doc__)
