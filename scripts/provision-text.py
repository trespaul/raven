#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request


# Raven Sans stands in for the dialog face Tahoma. It is DejaVu Sans Condensed with every advance narrowed so the weighted
# average width of Latin text matches Tahoma's, and with Tahoma's vertical metrics so a cell has the same height. The
# targets are the published figures of @capsizecss/metrics 4.4.0 (Tahoma: ascent 2049, descent 423, average 917 regular
# and 1044 bold on 2048 units); 937 and 1058 are the same average measured on the pinned DejaVu faces.
DIALOG_FACES = {
    "RavenSans-Regular.ttf": ("DejaVuSansCondensed.ttf", "Regular", 917 / 937),
    "RavenSans-Bold.ttf": ("DejaVuSansCondensed-Bold.ttf", "Bold", 1044 / 1058),
}
DIALOG_ASCENT = 2049
DIALOG_DESCENT = 423


def load_skia_manifest(manifest_path=None):
    path = manifest_path or Path(__file__).resolve().parent.parent / "native/graphics/skia.json"
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def load_fonts_manifest(manifest_path=None):
    path = manifest_path or Path(__file__).resolve().parent.parent / "native/graphics/fonts.json"
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


SKIA_ARGUMENTS = """is_official_build = true
is_debug = false
cc = "clang"
cxx = "clang++"
skia_enable_ganesh = false
skia_enable_graphite = false
skia_enable_pdf = false
skia_enable_skottie = false
skia_enable_svg = false
skia_enable_tools = false
skia_use_partition_alloc = false
skia_use_gl = false
skia_use_x11 = false
skia_use_fontconfig = false
skia_use_freetype = true
skia_use_harfbuzz = false
skia_use_icu = false
skia_use_expat = false
skia_use_piex = false
skia_use_wuffs = false
skia_use_libjpeg_turbo_decode = false
skia_use_libjpeg_turbo_encode = false
skia_use_libpng_decode = false
skia_use_libpng_encode = false
skia_use_libwebp_decode = false
skia_use_libwebp_encode = false
skia_use_zlib = false
skia_use_perfetto = false
skia_enable_fontmgr_empty = true
skia_enable_fontmgr_custom_empty = true
skia_use_system_freetype2 = true
"""


def ar_member(archive, prefix):
    at = 8
    while at + 60 <= len(archive):
        name = archive[at:at + 16].decode().strip()
        size = int(archive[at + 48:at + 58].decode())
        if name.startswith(prefix):
            return name, archive[at + 60:at + 60 + size]
        at += 60 + size + (size & 1)
    raise RuntimeError(f"the font package has no {prefix} member")


def provision_fonts(output, manifest=None):
    fonts = output / "fonts"
    fonts.mkdir(exist_ok=True)
    manifest = manifest or load_fonts_manifest()
    liberation = manifest["liberation"]
    package_url = liberation["url"]
    package_sha256 = liberation["sha256"]
    font_hashes = liberation.get("fonts", {})
    package = output / Path(package_url).name
    if not package.exists():
        partial = package.with_suffix(".part")
        urllib.request.urlretrieve(package_url, partial)
        partial.replace(package)
    data = package.read_bytes()
    if hashlib.sha256(data).hexdigest() != package_sha256:
        raise RuntimeError("font package checksum differs; delete it to download it again")
    name, payload = ar_member(data, "data.tar")
    tarball = output / name
    tarball.write_bytes(payload)
    subprocess.run(["tar", "-xf", tarball, "-C", fonts, "--strip-components=6", "--wildcards", "*/Liberation*-Regular.ttf"], check=True)
    tarball.unlink()
    for font, digest in font_hashes.items():
        if hashlib.sha256((fonts / font).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"font checksum differs: {font}")
    return fonts


def dialog_face(source, target, style, ratio):
    from fontTools.ttLib import TTFont

    font = TTFont(source, recalcTimestamp=False)
    metrics = font["hmtx"].metrics
    # Only the advances change: outlines, side bearings on the left and hinting stay as designed.
    for glyph, (advance, bearing) in metrics.items():
        metrics[glyph] = (round(advance * ratio), bearing)
    font["hhea"].ascent = DIALOG_ASCENT
    font["hhea"].descent = -DIALOG_DESCENT
    font["hhea"].lineGap = 0
    table = font["OS/2"]
    table.usWinAscent = table.sTypoAscender = DIALOG_ASCENT
    table.usWinDescent = DIALOG_DESCENT
    table.sTypoDescender = -DIALOG_DESCENT
    table.sTypoLineGap = 0
    # Version 1 of the table defines the average on lower-case letters, which narrow by the same ratio.
    table.xAvgCharWidth = round(table.xAvgCharWidth * ratio)
    font["hhea"].recalc(font)
    # The Bitstream Vera and Arev terms allow modified fonts only under names without their words; the notices stay.
    names = font["name"]
    full = "Raven Sans" if style == "Regular" else f"Raven Sans {style}"
    replaced = {1: "Raven Sans", 2: style, 3: f"Raven Sans {style} 2.37", 4: full, 5: "Version 2.37",
        6: f"RavenSans-{style}", 8: "Raven"}
    names.names = [record for record in names.names if record.nameID not in (16, 17)]
    for record in names.names:
        if record.nameID in replaced:
            record.string = replaced[record.nameID]
    names.setName("Derived from DejaVu Sans Condensed 2.37 with narrower advances and taller cells.", 10, 3, 1, 0x409)
    for word in ("Bitstream Vera", "Arev", "DejaVu Sans Condensed"):
        for record in names.names:
            if record.nameID in (1, 3, 4, 6) and word in str(record):
                raise RuntimeError(f"the dialog face is still named after {word}")
    font.save(target)


def provision_dialog_faces(output, fonts, manifest=None):
    manifest = manifest or load_fonts_manifest()
    dejavu = manifest["dejavu"]
    dejavu_url = dejavu["url"]
    dejavu_sha256 = dejavu["sha256"]
    archive = output / Path(dejavu_url).name
    if not archive.exists():
        partial = archive.with_suffix(".part")
        urllib.request.urlretrieve(dejavu_url, partial)
        partial.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != dejavu_sha256:
        raise RuntimeError("DejaVu release checksum differs; delete it to download it again")
    source = output / "dejavu"
    source.mkdir(exist_ok=True)
    # Python reads the bzip2 archive itself, so the host needs no bzip2 program.
    with tarfile.open(archive, "r:bz2") as release:
        for name in [f"ttf/{face}" for face, _, _ in DIALOG_FACES.values()] + ["LICENSE"]:
            member = release.extractfile(f"dejavu-fonts-ttf-2.37/{name}")
            (source / Path(name).name).write_bytes(member.read())
    for target, (face, style, ratio) in DIALOG_FACES.items():
        dialog_face(source / face, fonts / target, style, ratio)
    shutil.copyfile(source / "LICENSE", fonts / "RavenSans-LICENSE.txt")
    shutil.rmtree(source)


def find_freetype_include():
    pkg_config = shutil.which("pkg-config")
    if pkg_config:
        try:
            res = subprocess.run(
                [pkg_config, "--cflags-only-I", "freetype2"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for token in res.stdout.split():
                    if token.startswith("-I"):
                        inc_path = Path(token[2:].strip())
                        if (inc_path / "ft2build.h").exists():
                            return inc_path
                        if (inc_path / "freetype2/ft2build.h").exists():
                            return inc_path / "freetype2"
                        if inc_path.exists():
                            return inc_path
        except Exception:
            pass
    for candidate in [Path("/usr/include/freetype2"), Path("/usr/local/include/freetype2")]:
        if (candidate / "ft2build.h").exists():
            return candidate
    return None


def provision_skia(output, jobs, manifest=None, skia_source=None, freetype_include=None):
    if skia_source:
        source = skia_source.resolve()
    else:
        source = output / "skia"
        if not source.exists():
            manifest = manifest or load_skia_manifest()
            repository = manifest.get("url") or manifest.get("repository", "https://skia.googlesource.com/skia.git")
            commit = manifest.get("rev") or manifest.get("commit", "a21aae83d6e4e3da284100a30f0a5eafc443b60f")
            subprocess.run(["git", "init", "-q", source], check=True)
            subprocess.run(["git", "-C", source, "fetch", "-q", "--depth=1", repository, commit], check=True)
            subprocess.run(["git", "-C", source, "checkout", "-q", "FETCH_HEAD"], check=True)
            subprocess.run([sys.executable, "tools/git-sync-deps"], cwd=source, check=True)
    gn_bin = shutil.which("gn")
    if not gn_bin:
        gn_candidate = source / "bin/gn"
        if not gn_candidate.exists():
            subprocess.run([sys.executable, "bin/fetch-gn"], cwd=source, check=True)
        gn_bin = str(gn_candidate)
    ninja_bin = shutil.which("ninja")
    if not ninja_bin:
        ninja_candidate = source / "third_party/ninja/ninja"
        if not ninja_candidate.exists():
            subprocess.run([sys.executable, "bin/fetch-ninja"], cwd=source, check=True)
        ninja_bin = str(ninja_candidate)
    build = output / "cpu-fonts"
    build.mkdir(exist_ok=True)
    args_text = SKIA_ARGUMENTS
    if not freetype_include:
        freetype_include = find_freetype_include()
    if freetype_include:
        args_text += f'\nskia_system_freetype2_include_path = "{freetype_include}"\n'
    (build / "args.gn").write_text(args_text)
    subprocess.run([gn_bin, "gen", build], cwd=source, check=True)
    subprocess.run([ninja_bin, "-C", build, f"-j{jobs}", "skia"], check=True)
    return source, build / "libskia.a"


def main():
    parser = argparse.ArgumentParser(description="Provide the pinned Liberation fonts, the Raven Sans dialog faces and the CPU build of Skia that text in guest windows needs")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", "--skia-manifest", dest="manifest", type=Path, help="optional path to skia.json manifest")
    parser.add_argument("--fonts-manifest", type=Path, help="optional path to fonts.json manifest")
    parser.add_argument("--skia-source", type=Path, help="an existing checkout/directory of the Skia source")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--fonts-only", action="store_true", help="only the fonts, as Skia takes a long time to build")
    parser.add_argument("--skia-only", action="store_true", help="only the Skia library and source, skipping fonts")
    parser.add_argument("--freetype-include", type=Path, help="directory containing ft2build.h (defaults to pkg-config freetype2)")
    args = parser.parse_args()
    if args.fonts_only and args.skia_only:
        raise RuntimeError("--fonts-only and --skia-only cannot be used together")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tools = []
    if not args.skia_only:
        tools.append("tar")
    if not args.fonts_only:
        tools.extend(["clang", "clang++"])
        if not args.skia_source:
            tools.append("git")
    for tool in tools:
        if not shutil.which(tool):
            raise RuntimeError(f"required tool is missing: {tool}")
    fonts = None
    if not args.skia_only:
        fonts_manifest = load_fonts_manifest(args.fonts_manifest)
        fonts = provision_fonts(output, fonts_manifest)
        provision_dialog_faces(output, fonts, fonts_manifest)
        if args.fonts_only:
            print(f"configure Raven with -DRAVEN_FONT_DIRECTORY={fonts}")
            return
    manifest = load_skia_manifest(args.manifest) if not args.skia_source else None
    freetype_inc = args.freetype_include.resolve() if args.freetype_include else None
    source, library = provision_skia(
        output,
        args.jobs,
        manifest=manifest,
        skia_source=args.skia_source,
        freetype_include=freetype_inc,
    )
    if args.skia_only:
        print(f"configure Raven with -DRAVEN_SKIA_SOURCE={source} -DRAVEN_SKIA_LIBRARY={library}")
    else:
        print(f"configure Raven with -DRAVEN_SKIA_SOURCE={source} -DRAVEN_SKIA_LIBRARY={library} -DRAVEN_FONT_DIRECTORY={fonts}")


if __name__ == "__main__":
    os.umask(0o022)
    main()
