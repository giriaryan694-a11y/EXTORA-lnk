# EXTORA-lnk

Server-side `.lnk` generator with double-extension delivery via ZIP.

## What it does

Takes a target path, optional arguments, a display name, and a custom ZIP filename. Returns a ZIP containing a Windows shortcut (`.lnk`) named with the user-supplied double extension (e.g. `video.mp4.lnk`). 

The `.lnk` binary is built server-side by `lnksmith` per `[MS-SHLLINK]`. ZIP delivery avoids Chrome/Firefox `.lnk` download interception.

## Icon Support / Limitations

**Custom icons are intentionally not supported.** We attempted to implement this feature but hit a hard architectural limit of the Windows Shell Link format:

1. A `.lnk` file **does not embed** icon image bytes. It only stores a string path pointing to the icon file.
2. Relative paths (like `%cd%\icon.ico` or `.\icon.ico`) do not reliably resolve to the shortcut's directory in Windows.
3. When a `.lnk` is extracted from a ZIP to a target machine, it resolves absolute paths. If the icon file is placed next to the `.lnk`, the user would have to manually edit the shortcut properties to point to it, completely defeating the purpose of automation.
4. Using built-in system icons via environment variables (`%SystemRoot%\System32\imageres.dll`) proved unreliable across different Windows 10/11 builds due to shifting resource IDs.

Because there is no way to guarantee an icon renders correctly on the target machine without knowing the exact absolute path of an existing icon file, the feature was removed. The shortcut will use the default icon of its target executable.

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

