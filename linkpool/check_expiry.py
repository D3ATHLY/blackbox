"""Suresi yaklasan / dolmus havuz linklerini bildirir.

Action bu betigi her saat calistirir. Token'li linkler (mocha ~24s, viking ~48s)
kendiliginden olmeden once yenilenmesi icin issue acilir.

Cikti dosyalari (Action icin):
  <temp>/refresh-needed.txt : baslik metni ("PPSA38500 (mocha, viking)")
  <temp>/refresh-body.md    : issue govdesi
"""
from __future__ import annotations

import json
import os
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = os.path.join(HERE, "links")
WARN_HOURS = 8


def main() -> dict:
    now = time.time()
    soon, expired = [], []
    lines = []
    names = sorted(n for n in os.listdir(LINKS) if n.endswith(".json"))
    for name in names:
        with open(os.path.join(LINKS, name), encoding="utf-8") as fh:
            meta = json.load(fh)
        for entry in meta.get("links", []):
            exp = entry.get("expires")
            if not isinstance(exp, (int, float)):
                continue
            left = (exp - now) / 3600.0
            tag = f"{meta.get('titleId')}/{entry.get('provider')}"
            if left <= 0:
                expired.append(tag)
                lines.append(f"- `{tag}` **suresi doldu** ({abs(left):.1f} saat once)")
            elif left < WARN_HOURS:
                soon.append(tag)
                lines.append(f"- `{tag}` {left:.1f} saat sonra doluyor")
    tmp = tempfile.gettempdir()
    title_path = os.path.join(tmp, "refresh-needed.txt")
    body_path = os.path.join(tmp, "refresh-body.md")
    if soon or expired:
        with open(title_path, "w", encoding="utf-8") as fh:
            fh.write(", ".join(expired + soon))
        with open(body_path, "w", encoding="utf-8") as fh:
            fh.write("Havuzdaki token'li linkler yenilenmeli:\n\n" + "\n".join(lines))
            fh.write("\n\nYeni linkleri `linkpool/links/<TID>.json` icine ekleyin; "
                     "Action saatte bir dogrulayip yayinlar.\n")
    else:
        for p in (title_path, body_path):
            if os.path.exists(p):
                os.remove(p)
    print(json.dumps({"soon": soon, "expired": expired}, ensure_ascii=False))
    return {"soon": soon, "expired": expired}


if __name__ == "__main__":
    main()
