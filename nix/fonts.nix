{
  symlinkJoin,
  fetchurl,
  runCommand,
  binutils,
  zstd,
}:
let
  manifest = builtins.fromJSON (builtins.readFile ../native/graphics/fonts.json);
  archives = builtins.mapAttrs (_: value: fetchurl { inherit (value) url sha256; }) manifest;
  dejavu = runCommand "dejavu" { } ''
    mkdir -p $out
    tar --auto-compress --extract --strip-components=2 \
      --file ${archives.dejavu} \
      --directory $out
  '';
  liberation =
    runCommand "liberation"
      {
        nativeBuildInputs = [
          binutils
          zstd
        ];
      }
      ''
        mkdir -p $out
        ar -x ${archives.liberation}
        tar --auto-compress --extract --strip-components=6 \
          --file data.tar.zst \
          --directory $out
      '';
in
symlinkJoin {
  name = "raven-fonts";
  paths = [
    dejavu
    liberation
  ];
}
