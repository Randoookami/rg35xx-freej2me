#!/usr/bin/env bash
# Build the tested RGB565 libretro core using an existing RG35XX cross-toolchain Docker image.
# The FreeJ2ME Java JAR, private JRE and TF2 deployment are separate tasks.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/freej2me-plus-at-pinned-commit" >&2
  exit 2
fi

UPSTREAM="$(cd "$1" && pwd)"
PORT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_DIR:-$PORT_ROOT/out/rg35xx-rgb565}"
IMAGE="${TOOLCHAIN_IMAGE:-rg35xx-toolchain-cmake:latest}"
CROSS="/opt/miyoo/bin/arm-miyoo-linux-uclibcgnueabi-"
PIN="52b25f75824d247c23e352625be45157bfe87620"

[[ -f "$UPSTREAM/src/libretro/freej2me_libretro.c" ]] || {
  echo "Missing FreeJ2ME libretro sources" >&2
  exit 1
}

if [[ "$(git -C "$UPSTREAM" rev-parse HEAD)" != "$PIN" ]]; then
  echo "Refusing to build: FreeJ2ME source commit is not $PIN" >&2
  exit 1
fi
if [[ -e "$OUT" ]]; then
  echo "Refusing to overwrite existing output directory: $OUT" >&2
  exit 1
fi

mkdir -p "$OUT"
cp -a "$UPSTREAM/src/libretro/." "$OUT/"

# Use a clean copy of upstream source. Never patch the user's upstream checkout.
(
  cd "$OUT"
  patch -p3 < "$PORT_ROOT/patches/0001-rg35xx-rgb565.patch"
)

docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$OUT:/work" -w /work --entrypoint /bin/sh "$IMAGE" \
  -ec "
    set -e
    test -x ${CROSS}gcc
    make -j2 platform=unix \
      CC=${CROSS}gcc \
      CXX=${CROSS}gcc \
      AR=${CROSS}ar
  "

CORE="$OUT/freej2me_plus_libretro.so"
echo "=== Built core ==="
file "$CORE"
readelf -h "$CORE" | grep -E 'Class:|Machine:|Flags:'
readelf -d "$CORE" | grep NEEDED || true
sha256sum "$CORE"
echo "Output: $CORE"
