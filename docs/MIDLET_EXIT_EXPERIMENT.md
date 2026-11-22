# Experimental MIDlet exit -> RetroArch shutdown protocol

**Status: successful hardware exit and save regression tests in Bounce and Diamond Rush; no plug-and-play release yet.**

**Build result (2026-11-22):** On the original WSL development environment, both experimental components compiled successfully: `EXIT_EXPERIMENT_BUILD_OK`, `BUILD_EXIT_CODE=0`. Native core is ELF32 ARM EABI5 soft-float and directly links only `libc.so.0`. The Java libretro JAR compiled successfully using the Java 8 Docker image and Apache Ant. Build warnings about detached HEAD, apt/debconf and obsolete `-source 1.5` are non-fatal.

Verified experimental binary SHA-256 values:

```text
d133db3464bcd93417958bf087957cd2377866343a1fb4f13bdd260db4d74a69  freej2me_plus_libretro.so
79c049038530daf21b8e969e1c612d627d657d798510233409034f0483f7a867  freej2me_plus-lr.jar
```

Compilation and SHA-256 were verified in WSL; subsequent hardware tests confirmed game-menu exit to GarlicOS in both tested games. Both tested game saves persisted even after a device reboot; broader compatibility and crash-handling tests remain pending.

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

## First hardware result: core signal received, frontend remained open

On 2026-11-22, the Bounce exit test on RG35XX emitted:

```text
MIDlet normal exit requested; asking frontend to shut down.
```

The user reported the core/content exited into RetroArch's menu and had to choose **Quit RetroArch** manually to return to GarlicOS. The log then recorded `RETROARCH_EXIT_CODE=0`, but this proves **manual** RetroArch quit completed, not that the callback exited RetroArch on its own.

Hypothesis: the RetroArch option `load_dummy_on_core_shutdown = "true"` causes `RETRO_ENVIRONMENT_SHUTDOWN` to return to a dummy core/menu rather than quitting the frontend. The experiment's **TF2-only** append configuration now explicitly sets:

```ini
load_dummy_on_core_shutdown = "false"
```

**Retest result:** with this setting, Bounce returned directly to GarlicOS. Do not change the global TF1 RetroArch configuration.

## Second hardware result: automatic return to GarlicOS confirmed for Bounce

After changing only the **experimental** RetroArch append config on TF2 to:

```ini
load_dummy_on_core_shutdown = "false"
```

the user reported that choosing **Exit** within the Bounce game returned almost immediately to the GarlicOS game-selection menu from which `J2ME_Bounce_Exit_Test` was launched, without needing to choose `Quit RetroArch`.

**Hardware result: PASS for Bounce on the original RG35XX / GarlicOS 1.4.9.**

This corroborates that the `0xFD` MIDlet exit handshake and RetroArch shutdown environment request can work together, with dummy-core loading disabled. The earlier log already confirmed `MIDlet normal exit requested; asking frontend to shut down.`

**Diamond Rush exit subsequently verified;** manual RetroArch quit also passed on both games. In-game progress persisted across re-launches and full device reboot; crash handling remains untested.

## Third hardware result: Diamond Rush passed

On 2026-11-22, the user confirmed that **Diamond Rush also exits from its in-game menu directly back to GarlicOS**, using the same experimental 0xFD core and Java JAR pair and the test-only RetroArch configuration `load_dummy_on_core_shutdown = "false"`.

**Hardware result: PASS for Diamond Rush (exit behavior).** This is a user-observed result; no separate Diamond Rush log has yet been reviewed. Together with Bounce, two distinct MIDlets now demonstrate the intended behavior without game-specific patches.

### Pending regression before merging

- [x] Normal Quit RetroArch from a running test game still exits to GarlicOS (Bounce and Diamond Rush).
- [x] Restart both games; verify game progress and save persistence after in-game exit and full console reboot.
- [x] Confirm existing, non-experimental PORTS entries still launch and work; their old game-menu exit limitation remains as expected.
- [ ] Verify TF2 filesystem integrity independently, and test unintentional Java crashes; no such verification is claimed.

## Fourth hardware result: manual RetroArch quit still works

On 2026-11-22, the user confirmed that both test games also exit successfully using **Quick Menu → Main Menu → Quit RetroArch**, returning to GarlicOS. This is independent of the in-game MIDlet exit command.

**Hardware result: PASS for manual RetroArch exit in both Bounce and Diamond Rush.** This confirms the experimental integration does not remove the existing manual exit path in these tests.

## Fifth hardware result: persistence and legacy launcher regression

On 2026-11-22, the user reported **three successful final regression checks**:

- Both games launched again after a normal game-menu exit, and their **J2ME in-game progress persisted even after rebooting the RG35XX**.
- The original (non-experimental) PORTS entries still ran, and their in-game exit still had its original limitation, as expected.
- Manual RetroArch Quit and in-game Exit both returned to GarlicOS with the test build.

This verifies J2ME/RMS persistence in these game versions, **not libretro savestate support**.

## Related GarlicOS Recent limitation

GarlicOS 1.4.9's `Recent` menu shows **"This core doesn't support savestates!"** for the FreeJ2ME core, and the user reports its `X` removal action does not remove these game entries. FreeJ2ME-Plus 1.53's native core defines `retro_serialize_size() = 0` and leaves serialize/unserialize unimplemented; that is distinct from persistent in-game RMS saves. This is a separate integration issue; the exit patch does not claim to implement savestates. Preserve user saves and back up GarlicOS history before any manual editing.

## Hardware test preparation (already completed for first tests)

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

**Hardware exit and save regression passed for the two tested games.** Any merge should preserve the earlier known-good core as a backup; general game compatibility and savestates remain separate issues.
