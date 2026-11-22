#!/usr/bin/env python3
"""Apply a one-off, experimental MIDlet-exit protocol to a COPY of FreeJ2ME-Plus 1.53.

Expected input: a separate checkout at upstream commit
52b25f75824d247c23e352625be45157bfe87620.

The Java IO thread emits a reserved 0xFD marker after MIDlet.notifyDestroyed().
The libretro C core reads that marker and asks its frontend to shut down.

Do NOT apply this to your known-good FreeJ2ME sources or production core.
"""
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 apply-midlet-exit-experiment.py /path/to/EXPERIMENTAL/freej2me-source-copy")

    root = Path(sys.argv[1]).resolve()
    if not (root / "src/org/recompile/freej2me/Libretro.java").is_file():
        raise SystemExit("ERROR: FreeJ2ME-Plus source directory not found")

    edits = {
        "src/org/recompile/mobile/Mobile.java": [
            (
                "\tpublic static byte libretroRestartRequested = 0;",
                "\tpublic static volatile boolean libretroExitRequested = false; // Set only after a MIDlet calls notifyDestroyed()\n"
                "\tpublic static byte libretroRestartRequested = 0;",
            ),
        ],
        "src/javax/microedition/midlet/MIDlet.java": [
            (
                "\t\tMobile.midlet = null;\n",
                "\t\tMobile.midlet = null;\n"
                "\t\t// Let the libretro IO thread transmit the exit event, not the game thread.\n"
                "\t\tif (org.recompile.mobile.MobilePlatform.isLibretro)\n"
                "\t\t{\n"
                "\t\t\tMobile.libretroExitRequested = true;\n"
                "\t\t}\n",
            ),
        ],
        "src/org/recompile/freej2me/Libretro.java": [
            (
                "\t\t\t\t\t\t\tcase 15: // Libretro core requested a new frame.\n",
                "\t\t\t\t\t\t\tcase 15: // Libretro core requested a new frame.\n"
                "\t\t\t\t\t\t\t\t// Protocol 0xFD: an application requested a normal MIDlet exit.\n"
                "\t\t\t\t\t\t\t\t// Only this IO thread writes control bytes to stdout.\n"
                "\t\t\t\t\t\t\t\tif (Mobile.libretroExitRequested)\n"
                "\t\t\t\t\t\t\t\t{\n"
                "\t\t\t\t\t\t\t\t\tSystem.out.write(0xFD);\n"
                "\t\t\t\t\t\t\t\t\tSystem.out.flush();\n"
                "\t\t\t\t\t\t\t\t\tbreak;\n"
                "\t\t\t\t\t\t\t\t}\n",
            ),
        ],
        "src/libretro/freej2me_libretro.c": [
            (
                "\t\t\ti++;\n\t\t\tstatus = read_from_pipe(pRead[0], &t, 1);\n",
                "\t\t\ti++;\n\t\t\tstatus = read_from_pipe(pRead[0], &t, 1);\n"
                "\t\t\t/* Experimental Java-to-libretro control marker. */\n"
                "\t\t\tif(status == 1 && t == 0xFD)\n"
                "\t\t\t{\n"
                "\t\t\t\tlog_fn(RETRO_LOG_INFO, \"MIDlet normal exit requested; asking frontend to shut down.\\n\");\n"
                "\t\t\t\tif(!Environ(RETRO_ENVIRONMENT_SHUTDOWN, NULL))\n"
                "\t\t\t\t{\n"
                "\t\t\t\t\tlog_fn(RETRO_LOG_WARN, \"Frontend did not accept shutdown request.\\n\");\n"
                "\t\t\t\t}\n"
                "\t\t\t\treturn;\n"
                "\t\t\t}\n",
            ),
        ],
    }

    # Validate *all* anchors before writing any file: no partial modifications.
    changes = []
    for relative, replacements in edits.items():
        path = root / relative
        raw = path.read_bytes()
        nl = "\r\n" if b"\r\n" in raw else "\n"
        original = raw.decode("utf-8").replace("\r\n", "\n")
        updated = original
        for before, after in replacements:
            occurrences = updated.count(before)
            if occurrences != 1:
                raise SystemExit(f"ABORT: {relative}: expected anchor once, found {occurrences}")
            updated = updated.replace(before, after)
        changes.append((path, updated.replace("\n", nl).encode("utf-8")))

    for path, updated in changes:
        path.write_bytes(updated)
        print("PATCHED:", path.relative_to(root))

    print("MIDLET EXIT EXPERIMENT PATCHED: 0xFD protocol; frontend shutdown is not yet tested.")


if __name__ == "__main__":
    main()
