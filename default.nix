let
  nixpkgs = fetchTarball "https://channels.nixos.org/nixos-unstable/nixexprs.tar.zst";
  pkgs = import nixpkgs { };
in
rec {
  roots = pkgs.callPackage ./nix/roots.nix { };
  graphics = pkgs.callPackage ./nix/graphics.nix { };
  sqlite = pkgs.callPackage ./nix/sqlite.nix { };
  rtl = pkgs.callPackage ./nix/rtl.nix { };
  controls = pkgs.callPackage ./nix/controls.nix { };
  installer = pkgs.callPackage ./nix/installer.nix { };
  skia = pkgs.callPackage ./nix/skia.nix { };
  fonts = pkgs.callPackage ./nix/fonts.nix { };

  default = pkgs.callPackage ./nix/package.nix {
    inherit
      roots
      graphics
      sqlite
      rtl
      controls
      installer
      skia
      fonts
      ;
  };
}
