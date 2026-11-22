# Experimental MIDlet exit -> RetroArch shutdown protocol

**Status: untested on hardware. Draft change, NOT a stable release.**

**Build result (2026-11-22):** On the original WSL development environment, both experimental components compiled successfully: `EXIT_EXPERIMENT_BUILD_OK`, `BUILD_EXIT_CODE=0`. Native core is ELF32 ARM EABI5 soft-float and directly links only `libc.so.0`. The Java libretro JAR compiled successfully using the Java 8 Docker image and Apache Ant. Build warnings about detached HEAD, apt/debconf and obsolete `-source 1.5` are non-fatal.

Verified experimental binary SHA-256 values:

```text
d133db3464bcd93417958bf087957cd2377866343a1fb4f13bdd260db4d74a69  freej2me_plus_libretro.so
79c049038530daf21b8e969e1c612d627d657d798510233409034f0483f7a867  freej2me_plus-lr.jar
```

This is compilation verification only; MIDlet exit / RetroArch shutdown remains **untested on actual hardware**.

## Why a protocol change is needed

In upstream FreeJ2ME-Plus 1.53, `MIDlet.notifyDestroyed()` clears `Mobile.midlet`, but the libretro Java process remains alive, so the native core cannot distinguish an intentional app exit from ordinary idle frames.

The experimental modification adds a minimal explicit signal between the existing Java and C processes:

1. `MIDlet.notifyDestroyed()` sets a `volatile` `Mobile.libretroExitRequested` flag only in libretro mode.
2. On the next core frame request, the Java **IO thread** writes exactly one byte `0xFD` to its existing stdout pipe, instead of sending an ordinary `0xFE` frame marker/payload.
3. The C core recognizes `0xFD` while looking for the frame marker and calls `RETRO_ENVIRONMENT_SHUTDOWN`.
4. RetroArch should then quit normally, returning to GarlicOS because it was launched by a PORTS script.

No game JAR is changed. The original RGB565 patch is applied as a separate patch. This is not a generic Java-process-crash handler; it recognizes only explicit MIDlet shutdown.

## Building both modified components

On the established WSL workstation (Docker images already available):

```bash
ROOT="$HOME/rg35xx-freej2me"
PUB="$HOME/rg35xx-freej2me-public"

git -C "$PUB" fetch origin
git -C "$PUB" switch --track origin/experiment/midlet-exit-01

set -o pipefail
bash "$PUB/scripts/build-exit-experiment.sh" "$ROOT/sources/freej2me-plus" \
  2>&1 | tee "$ROOT/reports/midlet-exit-build-01.log"

echo "BUILD_EXIT_CODE=${PIPESTATUS[0]}"
```

The script creates an isolated source copy under `$PUB/out/midlet-exit-01/freej2me-plus`, and builds:

- `src/libretro/freej2me_plus_libretro.so` — patched native ARM32/RGB565 core.
- `build/freej2me_plus-lr.jar` — modified Java libretro application.

The stock native core/JAR and TF1/TF2 remain untouched. The public `main` branch remains unchanged.

## Hardware test design (not yet performed)

After both components build successfully, prepare an isolated TF2 staging directory on WSL with:

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" pull --ff-only
bash "$PUB/scripts/stage-exit-test.sh"
```

The script verifies the specific experimental binary hashes from build #1 before staging anything. It stages the experimental core, Java JAR, separate Java wrapper, test-only RetroArch append config and two PORTS launchers under `$PUB/out/exit-test-tf2-01/`. It **does not write to either SD card**.

The experimental core and modified libretro Java JAR **must be paired**. Copy neither over the working baseline.

Prepare a separate TF2 system directory and RetroArch append config:

```text
/mnt/SDCARD/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/java
/mnt/SDCARD/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/freej2me_plus-lr.jar
/mnt/SDCARD/J2ME/core/freej2me_plus_exit_test_libretro.so
/mnt/SDCARD/J2ME/config/freej2me-ra-exit-test.cfg
```

- The test `bin/java` is a **copy** of the working shell wrapper; it can still call the already tested private Java runtime under `/mnt/SDCARD/J2ME/runtime/`.
- The test config sets `system_directory` to `/mnt/SDCARD/J2ME/test-system` and preserves the existing save directory.
- The test launcher must explicitly use the experimental core, test config, and an existing legally obtained JAR.
- Check `chkdsk F:` before and after any hardware attempt; do not use this on TF1.

### Acceptance criteria

1. Bounce and Diamond Rush start and remain playable with Sound Off.
2. Exit from each game's own menu reaches the C log marker, requests frontend shutdown and returns to GarlicOS.
3. Exit via the RetroArch menu still works.
4. Game saves, regular game progression, config state and FAT32 remain intact.
5. An unexpected Java crash **does not** masquerade as a normal MIDlet exit.

If GarlicOS ignores `RETRO_ENVIRONMENT_SHUTDOWN`, keep the feature experimental and investigate frontend behavior rather than killing processes blindly.

## Rollback

Exit the test normally or through RetroArch. Launch the original Bounce/Diamond Rush PORTS entries (they still use the known-good core and normal BIOS runtime). Remove only the separate `J2ME/test-system`, `freej2me_plus_exit_test_libretro.so` and test launcher after preserving logs.

**Do not merge this experiment into `main` until actual hardware results are reviewed.**
