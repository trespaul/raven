{
  stdenv,
  fetchurl,
  pkgsCross,
  python3,
}:

let
  manifest = builtins.fromJSON (builtins.readFile ../native/nt/sqlite.json);
  archive = fetchurl {
    url = manifest.url;
    sha256 = manifest.sha256;
  };
in
stdenv.mkDerivation (finalAttrs: {
  pname = "raven-sqlite-component";
  version = "0.0.0";
  src = ../.;
  nativeBuildInputs = [
    python3
    pkgsCross.mingwW64.buildPackages.gcc
  ];

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild
    python3 scripts/provision-sqlite.py --archive ${archive} --output .
    mkdir $out
    mv ./winsqlite3.dll $out/
    runHook postBuild
  '';

  dontInstall = true;
})
