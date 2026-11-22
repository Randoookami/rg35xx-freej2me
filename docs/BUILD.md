# Source and build notes (experimental)

These are **recorded build facts and a native-core build recipe**, not a fully tested clean-room installer.

## Pin the upstream sources

```sh
git clone https://github.com/TASEmulators/freej2me-plus.git
cd freej2me-plus
git checkout 52b25f75824d247c23e352625be45157bfe87620
```

The tested FreeJ2ME libretro Java JAR was built with Apache Ant and Java 8, producing `build/freej2me_plus-lr.jar`. The desktop variant `build/freej2me_plus.jar` also built and ran on PC. The native C libretro core was cross-compiled separately.

## Native core cross-build

The original development environment used a Docker image named `rg35xx-toolchain-cmake:latest` with the `arm-miyoo-linux-uclibcgnueabi-` GCC 7.3.0 toolchain at `/opt/miyoo/bin/`. This image name is **local**, not a published reproducible dependency yet.

Run in a copy of `src/libretro`, **after** applying [the RGB565 patch](../patches/0001-rg35xx-rgb565.patch):

```sh
make -j2 platform=unix \
  CC=/opt/miyoo/bin/arm-miyoo-linux-uclibcgnueabi-gcc \
  CXX=/opt/miyoo/bin/arm-miyoo-linux-uclibcgnueabi-gcc \
  AR=/opt/miyoo/bin/arm-miyoo-linux-uclibcgnueabi-ar

file freej2me_plus_libretro.so
readelf -d freej2me_plus_libretro.so | grep NEEDED
```

Using GCC rather than G++ at link time avoided unnecessary direct dependencies on `libstdc++.so.6` and `libgcc_s.so.1`; the tested core depended directly only on `libc.so.0`.

The known-good RGB565 core SHA-256 was:

```text
555dd3ace94cd1076cedc1128d040b564d39014f59a111330607eee9c3bdd25e
```

This checksum identifies one historical locally built file; it may change across compiler or source changes.

## Reproducibility verified on 2026-11-22

The public repository was cloned fresh at commit `214efbd` on the original development WSL workstation. Running `scripts/build-core.sh` with the pinned upstream FreeJ2ME source and the existing Docker cross-toolchain completed successfully (`BUILD_EXIT_CODE=0`). The patched `src/libretro/freej2me_libretro.c` matched the previously tested source **byte for byte**, and the rebuilt ARM32 core had the **same SHA-256**:

```text
555dd3ace94cd1076cedc1128d040b564d39014f59a111330607eee9c3bdd25e
```

Verified ABI: ELF32 ARM EABI5 soft-float; direct dependency: `libc.so.0`.

**Scope:** This establishes a reproducible native build **in that existing toolchain/environment**. It is not yet an independent toolchain bootstrap or a verification of the complete Java/TF2 deployment. Keep the original working core as a regression baseline.

## Java runtime integration

The Java runtime is a **separate process**, not linked into the libretro core. The successful setup used Zulu 8u512 ARMHF, extracted Debian 11 ARMHF glibc 2.31 libraries, a copied `jre/bin/java` binary whose ELF interpreter was set with `patchelf` to the private TF2 loader path, and a shell wrapper to configure Java library search paths and reorder FreeJ2ME 1.53's launch arguments.

The tested original Java launcher gave an error locating `libjava.so` when directly invoked through `ld-linux-armhf.so.3`. Changing the **copy's ELF interpreter** permitted normal direct process execution while maintaining Java's home-directory detection.

For a description of exact TF2 paths and ABI boundaries see [Architecture](ARCHITECTURE.md).

## Not yet provided

- Fully automated Java-runtime packaging, hash verification and licensing review.
- Portable public Docker toolchain image/digest.
- Stable end-user install script.
- Reliable aspect-ratio, audio and exit handling.

Do not download from arbitrary mirrors or publish private vendor executables as project source.
