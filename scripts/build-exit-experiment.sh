#!/usr/bin/env bash
# EXPERIMENTAL: build both sides of the MIDlet-exit protocol from a clean local clone.
# No changes to the pinned upstream checkout, known-good core, TF1 or TF2.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/pinned/freej2me-plus" >&2
  exit 2
fi

UPSTREAM="$(cd "$1" && pwd)"
PORT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="${TEST_ROOT:-$PORT_ROOT/out/midlet-exit-01}"
PIN="52b25f75824d247c23e352625be45157bfe87620"
CROSS="/opt/miyoo/bin/arm-miyoo-linux-uclibcgnueabi-"
IMAGE="${TOOLCHAIN_IMAGE:-rg35xx-toolchain-cmake:latest}"

if [[ "$(git -C "$UPSTREAM" rev-parse HEAD)" != "$PIN" ]]; then
  echo "ABORT: upstream is not pinned to the tested commit $PIN" >&2
  exit 1
fi
if [[ -e "$TEST_ROOT" ]]; then
  echo "ABORT: test directory exists, no files overwritten: $TEST_ROOT" >&2
  exit 1
fi

mkdir -p "$TEST_ROOT"
git clone --local --no-hardlinks --quiet "$UPSTREAM" "$TEST_ROOT/freej2me-plus"
git -C "$TEST_ROOT/freej2me-plus" checkout --detach --quiet "$PIN"

SRC="$TEST_ROOT/freej2me-plus"
python3 "$PORT_ROOT/scripts/apply-midlet-exit-experiment.py" "$SRC"
patch -d "$SRC" -p1 < "$PORT_ROOT/patches/0001-rg35xx-rgb565.patch"

echo "=== BUILD ARM32 NATIVE CORE ==="
docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$SRC/src/libretro:/work" -w /work \
  --entrypoint /bin/sh "$IMAGE" \
  -ec "
    set -e
    test -x ${CROSS}gcc
    make -j2 platform=unix \
      CC=${CROSS}gcc CXX=${CROSS}gcc AR=${CROSS}ar
  "

echo "=== BUILD EXPERIMENTAL LIBRETRO JAVA JAR (JAVA 8) ==="
# Installs Ant only in a disposable container; the WSL OS is unchanged.
docker run --rm \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -v "$SRC:/work" -w /work \
  --entrypoint /bin/sh eclipse-temurin:8-jdk \
  -ec '
    set -e
    command -v ant >/dev/null 2>&1 || {
      apt-get update -qq
      apt-get install -y -qq ant
    }
    ant jar-libretro
    chown -R "$HOST_UID:$HOST_GID" build
  '

CORE="$SRC/src/libretro/freej2me_plus_libretro.so"
JAR="$SRC/build/freej2me_plus-lr.jar"

test -s "$CORE"
test -s "$JAR"

echo "=== EXPERIMENTAL BUILD OUTPUT ==="
file "$CORE"
readelf -h "$CORE" | grep -E 'Class:|Machine:|Flags:'
readelf -d "$CORE" | grep NEEDED || true
sha256sum "$CORE" "$JAR"
ls -lh "$CORE" "$JAR"
echo "EXIT_EXPERIMENT_BUILD_OK"
echo "SOURCE_COPY=$SRC"
