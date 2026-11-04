{
  linkFarmFromDrvs,
  fetchurl,
  runCommand,
  gnutar,
  gzip,
  zstd,
}:
let
  manifest = builtins.fromJSON (builtins.readFile ../native/graphics/backends.json);
  archives = builtins.mapAttrs (_: value: fetchurl { inherit (value) url sha256; }) manifest;
  extract =
    name:
    runCommand name
      {
        nativeBuildInputs = [
          gnutar
          gzip
          zstd
        ];
      }
      ''
        mkdir -p $out
        tar --auto-compress --extract --strip-components=1 \
          --file ${archives.${name}} \
          --directory $out
      '';
in
linkFarmFromDrvs "raven-graphics" (
  map extract [
    "vkd3d-proton"
    "dxvk"
  ]
)
