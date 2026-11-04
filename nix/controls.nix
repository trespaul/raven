{
  lib,
  stdenv,
  python3,
  pkgsCross,
  with32Bit ? true,
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "raven-controls";
  version = "0.0.0";
  src = ../.;
  nativeBuildInputs = [
    python3
    pkgsCross.mingwW64.buildPackages.gcc
  ]
  ++ lib.optional with32Bit pkgsCross.mingw32.buildPackages.gcc;

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild
    python3 scripts/provision-controls.py --output $out
    ${lib.optionalString with32Bit ''
      python3 scripts/provision-controls.py --arch x86 --output $out/x86
    ''}
    rm -rf $out/objects $out/x86/objects
    runHook postBuild
  '';

  dontInstall = true;
})
