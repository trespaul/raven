{
  stdenv,
  python3,
  pkgsCross,
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "raven-rtl";
  version = "0.0.0";
  src = ../.;
  nativeBuildInputs = [
    python3
    pkgsCross.mingwW64.buildPackages.gcc
  ];

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild
    python3 scripts/provision-rtl.py --output .
    mkdir $out
    mv ./raven-rtl.dll $out
    runHook postBuild
  '';

  dontInstall = true;
})

