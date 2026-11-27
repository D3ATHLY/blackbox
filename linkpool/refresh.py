"""Tek komutla link yenileme: yapistir -> dogrula -> yayina hazirla/yayinla.

Kullanim:
  python linkpool/refresh.py --tid PPSA38500            # sorar, dogrular, yerel JSON'u gunceller
  python linkpool/refresh.py --tid PPSA38500 --push     # ayrica GitHub'a commit eder (gh CLI)
  python linkpool/refresh.py --tid PPSA38500 --url "https://..." --provider mocha --push
  python linkpool/refresh.py --tid PPSA38500 --url "https://..." --dry-run

Davranis:
  * Saglayiciyi URL'den tahmin eder (mocha / viking / filekeeper / akirabox / vikingfile sayfasi).
  * Dogrudan (token'li) linklerde HTTP Range 0-1023 + PKG imzasi (7f464948) + boyut kontrolu yapar.
  * Sayfa linklerinde (filekeeper/akirabox) yalniz erisilebilirlik kontrolu yapar, requiresBrowser=true yazar.
  * Ayni saglayicinin eski kaydini degistirir; digerlerine dokunmaz.
  * --push: `gh api` ile linkpool/links/<TID>.json dosyasini main'e yazar (Action 1 saat icinde yayinlar).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = os.path.join(HERE, "links")
REPO = "D3ATHLY/blackbox"
PKG_MAGIC = bytes.fromhex("7f464948")
UA = "BlackBox-LinkPool/1.1 (+refresh)"


def guess_provider(url: str) -> tuple[str, bool]:
    """(provider, requiresBrowser)"""
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    if "mochaprox" in host:
        return "mocha", False
    if "cloud.ovh.net" in host or "X-Amz-Signature" in url:
        return "viking", False
    if "filekeeper" in host:
        return "filekeeper", True
    if "akirabox" in host:
        return "akirabox", True
    if "vikingfile" in host or "vik1ngfile" in host:
        return "vikingfile", True
    return "", True


def expiry_of(url: str) -> int | None:
    m = re.search(r"[?&]expires=(\d+)", url)
    if m:
        return int(m.group(1))
    m = re.search(r"X-Amz-Date=(\d{8})T(\d{6})Z", url)
    if m:
        base = time.mktime(time.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")) - time.timezone
        e = re.search(r"X-Amz-Expires=(\d+)", url)
        return int(base + int(e.group(1)) if e else base + 3600)
    return None


def probe(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-1023"})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            head = r.read(1024)
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            status = r.status
    except urllib.error.HTTPError as exc:
        return {"ok": False, "reason": f"HTTP {exc.code}", "ms": round((time.time() - started) * 1000)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)[:160], "ms": round((time.time() - started) * 1000)}
    total = None
    m = re.search(r"/(\d+)$", hdrs.get("content-range", ""))
    if m:
        total = int(m.group(1))
    elif hdrs.get("content-length", "").isdigit():
        total = int(hdrs["content-length"])
    return {
        "ok": status in (200, 206),
        "http": status,
        "bytes": total,
        "pkg_magic": head[:4] == PKG_MAGIC,
        "ms": round((time.time() - started) * 1000),
    }


def load(tid: str) -> dict:
    path = os.path.join(LINKS, tid + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"titleId": tid, "title": tid, "links": []}


def save_local(tid: str, data: dict) -> str:
    os.makedirs(LINKS, exist_ok=True)
    path = os.path.join(LINKS, tid + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def push(tid: str, path: str) -> dict:
    content = base64.b64encode(open(path, "rb").read()).decode()
    repo_path = f"linkpool/links/{tid}.json"
    sha = None
    p = subprocess.run(["gh", "api", f"repos/{REPO}/contents/{repo_path}"],
                       capture_output=True, text=True)
    if p.returncode == 0:
        sha = json.loads(p.stdout).get("sha")
    body = {"message": f"linkpool: {tid} link refresh",
            "content": content, "branch": "main"}
    if sha:
        body["sha"] = sha
    p = subprocess.run(["gh", "api", "-X", "PUT",
                        f"repos/{REPO}/contents/{repo_path}",
                        "--input", "-"],
                       input=json.dumps(body), capture_output=True, text=True)
    if p.returncode != 0:
        return {"ok": False, "error": (p.stderr or p.stdout).strip()[-300:]}
    return {"ok": True, "commit": json.loads(p.stdout).get("commit", {}).get("sha", "")[:8]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tid", default="PPSA38500")
    ap.add_argument("--url")
    ap.add_argument("--provider")
    ap.add_argument("--browser", action="store_true",
                    help="sayfa linki olarak kaydet (requiresBrowser)")
    ap.add_argument("--bytes", type=int, help="beklenen boyut (dogrudan linklerde)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    data = load(args.tid)
    url = (args.url or input("Linki yapistir: ")).strip()
    if not re.match(r"^https?://", url):
        print("Gecersiz URL.")
        return 2
    guessed, browser = guess_provider(url)
    provider = args.provider or guessed
    if args.browser:
        browser = True
    if not provider:
        provider = input("Saglayici adi (ornek: mocha, viking, filekeeper, akirabox): ").strip()
        if not provider:
            print("Saglayici gerekli.")
            return 2

    print(f"saglayici={provider}  tur={'sayfa' if browser else 'dogrudan'}")
    res = probe(url)
    print("kontrol:", json.dumps(res, ensure_ascii=False))
    if not res.get("ok"):
        print("LINK CALISMADI - kaydedilmedi.")
        return 1
    if not browser and not res.get("pkg_magic"):
        print("DIKKAT: PKG imzasi yok. Yine de kaydetmek icin --browser/--force kullanin.")
        return 1
    expect = args.bytes or next((l.get("verified_bytes") for l in data["links"]
                                 if l.get("provider") == provider), None)
    if expect and res.get("bytes") and res["bytes"] != expect:
        print(f"BOYUT FARKLI: {res['bytes']} != {expect}")
        return 1

    entry = {
        "provider": provider,
        "url": url,
        "verified_bytes": res.get("bytes") or expect,
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "added_by": os.environ.get("USERNAME") or "owner",
    }
    if browser:
        entry["requiresBrowser"] = True
    exp = expiry_of(url)
    if exp:
        entry["expires"] = exp
        print("son kullanma:", time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(exp)))

    links = [l for l in data["links"] if l.get("provider") != provider]
    links.append(entry)
    links.sort(key=lambda l: (l.get("expires") or 0))
    data["links"] = links

    if args.dry_run:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    path = save_local(args.tid, data)
    print("yazildi:", path)
    if args.push:
        out = push(args.tid, path)
        print("push:", json.dumps(out, ensure_ascii=False))
        if not out.get("ok"):
            return 1
        print("Action 1 saat icinde dogrulayip yayinlar (elle: gh workflow run linkpool).")
    else:
        print("Yayinlamak icin: --push (veya dosyayi commit edin)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
