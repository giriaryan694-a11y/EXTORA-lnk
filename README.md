# EXTORA-lnk

Server-side `.lnk` generator with double-extension delivery via ZIP.

## What it does

Takes a target path, optional arguments, a display name, and an optional icon. Returns a ZIP containing a Windows shortcut (`.lnk`) named with the user-supplied double extension (e.g. `video.mp4.lnk`), plus the uploaded icon when provided.

The `.lnk` binary is built server-side by `lnksmith` per `[MS-SHLLINK]`. ZIP delivery avoids Chrome/Firefox `.lnk` download interception.

Icon handling: uploaded `.ico`/`.png`/`.exe`/`.dll` is written into the ZIP next to the shortcut and referenced as `%cd%\icon.ico`, resolved at launch from the extraction folder.

## Live demo

https://extora-lnk.vercel.app/

## Stack

- Python 3 / Flask
- `lnksmith` (primary), `pylnk3` (fallback)
- Vercel Python serverless runtime

## Ethical disclaimer

This is dual-use software. The double-extension shortcut technique maps to MITRE ATT&CK **T1036.007** (Masquerading: Double File Extension) and is used in real-world phishing and initial-access campaigns. It is equally applicable to legitimate uses — red-team engagement tooling, security awareness training, CTF challenges, detection engineering, and authorized penetration testing.

You are responsible for how you use it. Using this tool to deceive, gain unauthorized access to systems you do not own or have explicit written permission to test, or to deliver payloads to third parties is illegal in most jurisdictions under computer misuse laws (e.g. CFAA in the US, Computer Misuse Act in the UK, IT Act 2000 in India). The author accepts no liability for misuse.

Use only on systems you own or are authorized to test.

## License

Licensed under the Apache License, Version 2.0.
