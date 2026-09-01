"""IIS / SmarterASP startup entry (HttpPlatformHandler)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
packages = os.path.join(ROOT, "packages")
if os.path.isdir(packages):
    sys.path.insert(0, packages)

port = int(os.environ.get("HTTP_PLATFORM_PORT") or os.environ.get("PORT") or "8010")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
