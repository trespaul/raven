#!/usr/bin/env python3
"""Download the root certificates Windows trusts for code signing that host certificate bundles leave out.

Every Windows installation carries the Microsoft code signing roots in its root store, and installers check the signatures of the
packages they unpack against them. They come from Microsoft's public certificate repository, each checked against its pinned digest.

usage: provision-roots.py --output DIRECTORY
"""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def load_roots(manifest_path=None):
    path = manifest_path or Path(__file__).resolve().parent.parent / "native/nt/roots.json"
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def main():
    parser = argparse.ArgumentParser(description="Download the Microsoft code signing roots Windows trusts")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, help="optional path to roots.json manifest")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    roots = load_roots(args.manifest)
    entries = roots if isinstance(roots, list) else [{"name": k, **v} for k, v in roots.items()]
    for item in entries:
        name = item["name"]
        url = item["url"]
        digest = item["sha256"]
        target = args.output / name
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            with urllib.request.urlopen(url) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError(f"{name} differs from the pinned certificate")
            target.write_bytes(data)
    print(f"roots in {args.output}")


if __name__ == "__main__":
    main()
