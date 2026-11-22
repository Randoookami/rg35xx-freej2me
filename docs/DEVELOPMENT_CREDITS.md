# Development credits and AI assistance

## Full ChatGPT-assisted development project

This RG35XX FreeJ2ME-Plus port is developed through **extensive collaboration with OpenAI ChatGPT**.

**ChatGPT (OpenAI) — primary development assistant**
- Architecture exploration and technical research.
- Proposals for FreeJ2ME-Plus source patches, native/Java integration and video format conversion.
- Debugging analysis, test plans, build scripts and experimental changes.
- GitHub documentation, issue tracking, review of logs and organization of the development workflow.

**[Randoookami](https://github.com/Randoookami) — project owner, build operator and hardware tester**
- Provides the project objective, practical constraints and development priorities.
- Runs the WSL/Docker toolchains and builds, installs and tests on the original RG35XX.
- Supplies hardware diagnostics, technical logs and direct feedback from game tests.
- Validates whether proposed fixes actually work, including save persistence after device reboot.
- Controls the GitHub repository and accepts responsibility for the contents published under that account.

This statement is intended to **clearly acknowledge substantial AI involvement** while accurately recording that all claimed physical hardware results were established by human-run testing. ChatGPT does not possess or operate the user's RG35XX or WSL workstation directly; no AI-only hardware validation is implied.

## Upstream authors and third parties

The port is based on **[TASEmulators/FreeJ2ME-Plus](https://github.com/TASEmulators/freej2me-plus)**. The upstream authors and contributors retain their original copyright and licensing notices. The code is licensed GPL-3.0-or-later, subject to the upstream notices; bundled ObjectWeb ASM retains its own license terms. See [LICENSE](../LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md).

**No endorsement by OpenAI, TAS Emulators, Anbernic or GarlicOS is claimed.** This is an unofficial community initiative.

## Working principles

- Validate on actual hardware before claiming success.
- Publish the source code and document how modifications differ from upstream.
- Maintain a known-good RGB565 baseline and use separate branches for new experiments.
- Prefer generic emulator fixes and per-game data profiles over patching commercial game JAR files.
- Do not publish copyrighted commercial games, user saves, diagnostics with sensitive information, or vendor runtimes without checking redistribution terms.
