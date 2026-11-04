{
  lib,
  stdenv,
  fetchgit,
  python3,
  clang,
  pkg-config,
  freetype,
  gn,
  ninja,
}:

let
  manifest = builtins.fromJSON (builtins.readFile ../native/graphics/skia.json);
  source = fetchgit {
    inherit (manifest) url rev hash;
  };
in
stdenv.mkDerivation (finalAttrs: {
  pname = "raven-skia";
  version = "0.0.0";
  src = ../.;
  nativeBuildInputs = [
    python3
    clang
    pkg-config
    gn
    ninja
  ];

  buildInputs = [ freetype ];

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild
    python3 scripts/provision-text.py \
      --skia-only \
      --skia-source ${source} \
      --output $out
    cp -r ${source} $out/source
    runHook postBuild
  '';

  dontInstall = true;
})
