{
  lib,
  stdenv,
  fetchurl,
  python3,
  clang,
  wine,
  bison,
  pkgsCross,
  with32Bit ? true,
}:

let
  manifest = builtins.fromJSON (builtins.readFile ../native/nt/installer.json);
  archive = fetchurl {
    inherit (manifest) url sha256;
  };
in
stdenv.mkDerivation (finalAttrs: {
  pname = "raven-installer";
  version = "0.0.0";
  src = ../.;
  nativeBuildInputs = [
    python3
    clang
    wine
    bison
    pkgsCross.mingwW64.buildPackages.gcc
  ]
  ++ lib.optionals with32Bit [
    pkgsCross.mingw32.buildPackages.gcc
  ];

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild
    python3 scripts/provision-installer.py --archive ${archive} --output $out
    ${lib.optionalString with32Bit ''
      python3 scripts/provision-controls.py --arch x86 --output $out/x86
    ''}
    rm -rf $out/objects $out/x86/objects
    runHook postBuild
  '';

  dontInstall = true;
})
