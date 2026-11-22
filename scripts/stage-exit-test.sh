#!/usr/bin/env bash
# Stage an isolated RG35XX MIDlet-exit test on the host (no SD writes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/out/midlet-exit-01/freej2me-plus"
STAGE="$ROOT/out/exit-test-tf2-01"
CORE="$SOURCE/src/libretro/freej2me_plus_libretro.so"
JAR="$SOURCE/build/freej2me_plus-lr.jar"
EXPECTED_CORE="d133db3464bcd93417958bf087957cd2377866343a1fb4f13bdd260db4d74a69"
EXPECTED_JAR="79c049038530daf21b8e969e1c612d627d657d798510233409034f0483f7a867"

test -f "$CORE" && test -f "$JAR" || { echo "Build both experimental components first" >&2; exit 1; }
test ! -e "$STAGE" || { echo "Refusing to overwrite $STAGE" >&2; exit 1; }
test "$(sha256sum "$CORE" | cut -d' ' -f1)" = "$EXPECTED_CORE" || { echo "Core hash mismatch" >&2; exit 1; }
test "$(sha256sum "$JAR" | cut -d' ' -f1)" = "$EXPECTED_JAR" || { echo "JAR hash mismatch" >&2; exit 1; }

mkdir -p "$STAGE/J2ME/core" "$STAGE/J2ME/config" \
  "$STAGE/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin" "$STAGE/Roms/PORTS"
cp "$CORE" "$STAGE/J2ME/core/freej2me_plus_exit_test_libretro.so"
cp "$JAR" "$STAGE/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/freej2me_plus-lr.jar"

cat > "$STAGE/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/java" <<'JAVA'
#!/bin/sh
CARD="/mnt/SDCARD"
JRE="$CARD/J2ME/runtime/java8/jre"
GLIBC="$CARD/J2ME/runtime/glibc/lib/arm-linux-gnueabihf"
LOG="$CARD/J2ME/logs/java-stderr-exit-test.log"
mkdir -p "$CARD/J2ME/logs"
export LD_LIBRARY_PATH="$JRE/lib/aarch32/client:$JRE/lib/aarch32:$JRE/lib/aarch32/jli:$GLIBC"
if [ "$1" = "-jar" ] && [ "$#" -ge 3 ]; then
  shift
  ENCODING="$1"; shift
  JAR="$1"; shift
  set -- "$ENCODING" "-jar" "$JAR" "$@"
fi
exec "$JRE/bin/java" -Xms16m -Xmx96m -Djava.awt.headless=true \
  -Dsun.java2d.fontpath="$JRE/lib/fonts" "$@" 2>>"$LOG"
JAVA

cat > "$STAGE/J2ME/config/freej2me-ra-exit-test.cfg" <<'CFG'
system_directory = "/mnt/SDCARD/J2ME/test-system"
savefile_directory = "/mnt/SDCARD/J2ME/test-saves"
savestate_directory = "/mnt/SDCARD/J2ME/test-saves"
config_save_on_exit = "false"
CFG

for GAME in Bounce DiamondRush; do
  case "$GAME" in
    Bounce) ROM="Bounce.jar";;
    DiamondRush) ROM="Diamond Rush.jar";;
  esac
  DEST="$STAGE/Roms/PORTS/J2ME_"$GAME"_Exit_Test.sh"
  cat > "$DEST" <<'LAUNCHER'
#!/bin/sh
CARD="/mnt/SDCARD"
RA="/mnt/mmc/CFW/retroarch/retroarch"
CORE="$CARD/J2ME/core/freej2me_plus_exit_test_libretro.so"
CFG="$CARD/J2ME/config/freej2me-ra-exit-test.cfg"
SYSTEM="$CARD/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin"
LOGDIR="$CARD/J2ME/logs"
ROM_PLACEHOLDER
LOG_PLACEHOLDER
mkdir -p "$LOGDIR" "$CARD/J2ME/test-saves"
{
  echo "=== FreeJ2ME experimental exit test ==="
  echo "ROM=$ROM"
  for F in "$RA" "$CORE" "$CFG" "$ROM" "$SYSTEM/java" "$SYSTEM/freej2me_plus-lr.jar"; do
    if [ ! -f "$F" ]; then echo "MISSING: $F"; sync; exit 1; fi
    echo "OK: $F"
  done
  echo "=== RETROARCH START ==="
  export HOME="/mnt/mmc/CFW/retroarch"
  "$RA" -v --appendconfig "$CFG" -L "$CORE" "$ROM"
  RC=$?
  echo "RETROARCH_EXIT_CODE=$RC"
  echo "=== TEST FINISHED ==="
} > "$LOG" 2>&1
sync
exit 0
LAUNCHER
  python3 - "$DEST" "$ROM" "$GAME" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text()
assert text.count("ROM_PLACEHOLDER") == 1
assert text.count("LOG_PLACEHOLDER") == 1
text = text.replace("ROM_PLACEHOLDER", 'ROM="$CARD/Roms/JAVA/' + sys.argv[2] + '"')
text = text.replace("LOG_PLACEHOLDER", 'LOG="$LOGDIR/freej2me-exit-test-' + sys.argv[3].lower() + '.log"')
p.write_text(text)
PY
  chmod +x "$DEST"
  sh -n "$DEST"
done
chmod +x "$STAGE/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/java"
sh -n "$STAGE/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin/java"
echo "=== STAGED TF2 FILES ==="
(cd "$STAGE" && find . -type f -print | sort)
echo "EXIT_TEST_STAGE_OK: $STAGE"
