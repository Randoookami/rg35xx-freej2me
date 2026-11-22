# Third-party components and redistribution

This is an unofficial adaptation and **not** an upstream FreeJ2ME-Plus release.

## FreeJ2ME-Plus

- Upstream: https://github.com/TASEmulators/freej2me-plus
- Source revision tested: `52b25f75824d247c23e352625be45157bfe87620` (tag 1.53)
- FreeJ2ME code uses **GNU GPL version 3 or later**; the upstream `LICENSE` includes copyright notices, the full GPLv3 text, and ObjectWeb ASM's separate BSD-style terms.
- Keep original license/copyright headers and mark port modifications. Before shipping an executable core/JAR, provide corresponding complete source and build scripts in accordance with the license.

## Java and operating-system libraries

Tested external components, distributed by their respective maintainers:

- Azul Zulu OpenJDK 8u512, Linux `aarch32hf`, from https://www.azul.com/downloads/
- Debian Bullseye ARMHF `libc6` 2.31-13+deb11u14 and `libgcc-s1` 10.2.1-6, from Debian package archives.
- Existing GarlicOS/RetroArch and toolchain components supplied separately.

This repository **does not bundle** external Java runtimes, Debian libraries, GarlicOS images or toolchains. Consult each component's exact distribution license before creating binary release archives.

## Games and personal data

**Never commit game ROMs/JARs/JADs, game artwork or soundfonts of uncertain redistribution status, personal saves, crash dumps or logs containing identifying data.** Users must supply their own lawfully obtained game copies.

## Documentation and portability

Command paths in build notes describe a particular historical workspace and do not imply that those files exist on other computers. Verify any script on a clean checkout before claiming a reproducible release.
