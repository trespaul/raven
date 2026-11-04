{
  lib,
  stdenv,
  # testers,
  # nix-update-script,

  # nativeBuildInputs
  cmake,
  python3,
  pkg-config,
  wayland-scanner,
  binutils,
  pkgsCross,

  # buildInputs
  freetype,
  libpng,
  libxkbcommon,
  openssl,
  pixman,
  vulkan-headers,
  vulkan-loader,
  wayland,
  wayland-protocols,
  libxcb,
  libGL,
  libGLU,

  # resources fetched
  roots,
  graphics,

  # resources built
  rtl,
  controls,
  installer,
  sqlite,
  skia,
  fonts,

  # options
  withWayland ? true,
  withX11 ? false,
  withDirect3D ? true,
  withVulkan32 ? true,
  withOpenGL ? true,
  withDesktop ? true,
  withIcons ? true,
  withText ? true,
  withCrypto ? true,
  withInstaller ? true,
  withAuthenticode ? true,
  withSqlite ? true,
  withTests ? true,
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "raven";
  version = "0.0.0";

  src = ../.;

  nativeBuildInputs = [
    cmake
    pkg-config
    python3
  ]
  ++ lib.optionals withWayland [
    wayland-scanner
  ]
  ++ lib.optionals withVulkan32 [
    binutils
    pkgsCross.mingw32.buildPackages.gcc
  ];

  buildInputs =
    lib.optionals withDesktop [
      pixman
      libxkbcommon
    ]
    ++ lib.optionals withIcons [
      libpng
    ]
    ++ lib.optionals withText [
      freetype
    ]
    ++ lib.optionals withDirect3D [
      vulkan-headers
      vulkan-loader
    ]
    ++ lib.optionals withWayland [
      wayland
      wayland-protocols
    ]
    ++ lib.optionals withX11 [
      libxcb
    ]
    ++ lib.optionals withCrypto [
      openssl
    ]
    ++ lib.optionals withOpenGL [
      libGL
      libGLU
    ];

  cmakeFlags = [
    (lib.cmakeBool "RAVEN_SKIP_FIXTURE_DOWNLOADS" true)
  ]
  ++ lib.optionals withAuthenticode [
    (lib.cmakeFeature "RAVEN_ROOT_CERTIFICATE_DIRECTORY" (toString roots))
  ]
  ++ lib.optionals withText [
    (lib.cmakeFeature "RAVEN_SKIA_SOURCE" "${skia}/source")
    (lib.cmakeFeature "RAVEN_SKIA_LIBRARY" "${skia}/cpu-fonts/libskia.a")
    (lib.cmakeFeature "RAVEN_FONT_DIRECTORY" "${fonts}")
  ]
  ++ lib.optionals (!withWayland) [
    (lib.cmakeBool "RAVEN_DESKTOP_WAYLAND" false)
  ]
  ++ lib.optionals withX11 [
    (lib.cmakeBool "RAVEN_DESKTOP_X11" true)
  ]
  ++ lib.optionals withOpenGL [
    (lib.cmakeBool "RAVEN_OPENGL" true)
  ]
  ++ lib.optionals withTests [
    (lib.cmakeFeature "RAVEN_RTL_COMPONENT_PATH" "${rtl}/raven-rtl.dll")

    (lib.cmakeFeature "RAVEN_CONTROLS_COMPONENT_DIR" "${controls}")
    (lib.cmakeFeature "RAVEN_CONTROLS32_COMPONENT_DIR" "${controls}/x86/")

    (lib.cmakeFeature "RAVEN_INSTALLER_COMPONENT_DIR" "${installer}")
    (lib.cmakeFeature "RAVEN_INSTALLER32_COMPONENT_DIR" "${installer}/x86/")

    (lib.cmakeFeature "RAVEN_DXVK_PE64_DIR" "${graphics}/dxvk/x64/")
    (lib.cmakeFeature "RAVEN_DXVK_PE32_DIR" "${graphics}/dxvk/x32/")
    (lib.cmakeFeature "RAVEN_VKD3D_PE64_DIR" "${graphics}/vkd3d-proton/x64/")

    (lib.cmakeFeature "RAVEN_SQLITE_COMPONENT_DIR" (toString sqlite))
  ];

  # TODO: other test fixtures? [needs MinGW compilers in nativeBuildInputs]

  # TODO: runtime deps
  # - RTL components
  # - if desktop
  #   - controls components
  # - if installers
  #   - installer components
  # - if Direct3D
  #   - dxvk & vkd3d-proton
  # - if Authenticode
  #   - roots
  # - if GDI text
  #   - fonts
  # - if sqlite
  #   - sqlite

  passthru = {
    # tests.version = testers.testVersion {
    #   package = finalAttrs.finalPackage;
    #   command = "${lib.getExe finalAttrs.finalPackage} --version";
    # };
    # updateScript = nix-update-script { };
  };

  __structuredAttrs = true;

  meta = {
    description = "Run Windows applications on Linux directly on the CPU in a supervised guest process.";
    mainProgram = "raven";
    homepage = "https://useraven.org/";
    license = lib.licenses.gpl3Plus; # TODO
    maintainers = with lib.maintainers; [ trespaul ];
    platforms = [ "x86_64-linux" ];
  };
})
