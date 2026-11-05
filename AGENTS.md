# Project instructions

Read README.md and versions.json before changing the project. Prefix shell commands with rtk; use rtk proxy when raw output is needed.

Build from cataloged original APKs using recipes and scripts/build.py. Keep all repository file paths relative. Android virtual/system paths in Smali are device paths and must not be rewritten as host-relative paths.

The development signing key and password under signing/ are intentionally public and included in Git at the user's explicit request. Preserve this identity and com.dunehd.pcm for compatible updates unless the user requests a change. Do not introduce personal or production credentials.

Keep APK binaries, downloaded tools, Python environments and decoded build trees out of Git. Developers place original APKs locally in apks/original; built mods go in apks/mod. versions.json records original:mod mappings and SHA-256. Increase versionCode for a new release and keep existing published mappings.

## First build with a developer

Before the first build in a developer session, resolve these choices with the developer. Do not rebuild merely because an agent has connected to the repository. Reuse choices already explicitly confirmed in the conversation.

1. Inspect versions.json and APKs in apks/original. Ask which original APK / cataloged release to use; show available candidates and the current release. If none exists, ask the developer to place their original APK in apks/original. Verify its SHA-256 against the chosen original entry before applying a recipe. A new or mismatched APK needs its own catalog entry and verified recipe; never bypass checks or reuse native offsets blindly.
2. Ask which signing identity to use: the public development key in signing/ (recommended for compatible updates of this mod), an existing developer-owned keystore, or a newly generated key. Do not silently choose or generate a key. Explain that changing the certificate prevents updating an installed copy signed with the previous key.
3. For a custom key, use ignored signing/local/ for the keystore and password file; never stage these files or print passwords. Configure the local versions.json signing fields (relative keystore/passwordFile paths, alias, certificateSha256, publicDevelopmentKey=false) for both build and verification. Keep this machine-specific configuration out of the staged/public catalog and preserve the shared key files. Do not overwrite published release hashes with an APK signed by a different identity; agree a separate release before recording it.

Do not claim Android UI or playback success from static checks, DEX interpretation or native emulation. No device installation or deployment without explicit user authorization. Do not publish or push releases unless requested.
