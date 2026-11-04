{
  linkFarmFromDrvs,
  fetchurl,
}:

# download and collect symlinks to certificates
linkFarmFromDrvs "raven-roots" (
  map (cert: fetchurl { inherit (cert) url sha256; }) (
    builtins.fromJSON (builtins.readFile ../native/nt/roots.json)
  )
)
