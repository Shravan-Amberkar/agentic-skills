#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["kokoro-onnx>=0.6", "soundfile>=0.12", "playwright>=1.50"]
# ///
"""Record a narrated walkthrough of a running web app: browser video + offline neural voiceover.

    uv run record.py setup                         # one time: Chromium + Kokoro voice model (~350 MB)
    uv run record.py check  demo.json              # validate, voice every step, print the timing (no browser)
    uv run record.py record demo.json [--frames]   # record -> MP4 with voiceover and on-screen captions
    uv run record.py voices "A sample sentence."   # one WAV per voice, to pick one by ear

Everything runs locally: Playwright drives Chromium, Kokoro (Apache-2.0) speaks offline, ffmpeg
lays each narration clip at the moment its step started. Nothing is sent to a cloud service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

MODELS_DIR = Path(os.environ.get("DEMO_MODELS_DIR", Path.home() / ".cache" / "demo-video-recorder"))
MODEL_FILES = {  # name -> (url, sha256)
    "kokoro-v1.0.onnx": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
                         "beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a"),
    "voices-v1.0.bin": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
                        "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"),
}
# Kokoro voice id prefix -> espeak language
LANGS = {"a": "en-us", "b": "en-gb", "h": "hi", "e": "es", "f": "fr-fr", "i": "it", "j": "ja", "p": "pt-br", "z": "cmn"}
DEFAULTS = {"viewport": [1440, 900], "voice": "am_michael", "speed": 1.2, "pad": 0.35, "tail_ms": 800, "captions": True}
TOP_KEYS = {"url", "output", "viewport", "voice", "lang", "speed", "pad", "tail_ms", "captions", "storage_state",
            "setup", "steps"}
ACTIONS = {"goto", "click", "fill", "type", "press", "hover", "scroll", "top", "wait", "wait_for", "eval"}
ACTION_EXTRAS = {"text", "selector", "block", "delay"}

CAPTION_CSS = """
#demo-cap{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);max-width:1100px;z-index:2147483647;
 background:rgba(18,24,38,.92);color:#fff;font:600 21px/1.4 Inter,system-ui,sans-serif;padding:14px 22px;
 border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.25);text-align:center;pointer-events:none}
"""


class ScriptError(ValueError):
    pass


# --------------------------------------------------------------------------- script

def action_kind(a: dict) -> str:
    kinds = [k for k in a if k in ACTIONS]
    if len(kinds) != 1:
        raise ScriptError(f"action {a!r} must have exactly one of {sorted(ACTIONS)}")
    unknown = set(a) - ACTIONS - ACTION_EXTRAS
    if unknown:
        raise ScriptError(f"action {a!r} has unknown keys {sorted(unknown)}")
    return kinds[0]


def load_script(path: Path) -> dict:
    """Read and validate a demo script; returns it with defaults filled in."""
    try:
        s = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ScriptError(f"{path}: not valid JSON: {e}") from e
    return validate(s)


def validate(s: dict) -> dict:
    if not isinstance(s, dict):
        raise ScriptError("script must be a JSON object")
    unknown = {k for k in s if not k.startswith("_")} - TOP_KEYS
    if unknown:
        raise ScriptError(f"unknown top-level keys {sorted(unknown)} (prefix notes with '_')")
    if not isinstance(s.get("url"), str) or not s["url"].startswith(("http://", "https://")):
        raise ScriptError("'url' must be an http(s) URL of the running app")
    steps = s.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ScriptError("'steps' must be a non-empty list")
    for i, st in enumerate(steps, 1):
        if not isinstance(st, dict) or not isinstance(st.get("say"), str) or not st["say"].strip():
            raise ScriptError(f"step {i}: 'say' (the narration) is required")
        if set(st) - {"say", "caption", "actions"}:
            raise ScriptError(f"step {i}: unknown keys {sorted(set(st) - {'say', 'caption', 'actions'})}")
        for a in st.get("actions", []):
            action_kind(a)
    for a in s.get("setup", []):
        action_kind(a)
    out = {**DEFAULTS, **s}
    out.setdefault("output", "demo.mp4")
    out.setdefault("lang", LANGS.get(out["voice"][:1], "en-us"))
    return out


# --------------------------------------------------------------------------- voice

def ensure_models() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, (url, sha) in MODEL_FILES.items():
        dest = MODELS_DIR / name
        if dest.exists() and _sha256(dest) == sha:
            continue
        print(f"downloading {name} ...", flush=True)
        tmp = dest.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 (fixed https URL, checksum verified below)
        if _sha256(tmp) != sha:
            tmp.unlink()
            raise SystemExit(f"{name}: checksum mismatch, download discarded")
        tmp.rename(dest)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Voice:
    """Kokoro when the model files are present, else macOS `say` (lower quality), else an error."""

    def __init__(self, voice: str, lang: str, speed: float):
        self.voice, self.lang, self.speed = voice, lang, speed
        self.kokoro = None
        if voice != "say" and (MODELS_DIR / "kokoro-v1.0.onnx").exists():
            from kokoro_onnx import Kokoro
            self.kokoro = Kokoro(str(MODELS_DIR / "kokoro-v1.0.onnx"), str(MODELS_DIR / "voices-v1.0.bin"))
        elif platform.system() != "Darwin":
            raise SystemExit("No voice model. Run `uv run record.py setup` first.")
        elif voice != "say":
            print("note: Kokoro model missing, using macOS `say`. Run `setup` for the better voice.", file=sys.stderr)

    def speak(self, text: str, path: Path) -> float:
        """Write narration for `text` to `path` (WAV/AIFF) and return its length in seconds."""
        import soundfile as sf
        if self.kokoro:
            audio, sr = self.kokoro.create(text, voice=self.voice, speed=self.speed, lang=self.lang)
            sf.write(str(path), audio, sr)
            return len(audio) / sr
        path = path.with_suffix(".aiff")
        subprocess.run(["say", "-r", str(int(175 * self.speed)), "-o", str(path), text], check=True)
        return sf.info(str(path)).duration


def synthesize(script: dict, work: Path) -> list[tuple[Path, float]]:
    v = Voice(script["voice"], script["lang"], script["speed"])
    clips = []
    for i, st in enumerate(script["steps"]):
        p = work / f"s{i:02d}.wav"
        dur = v.speak(st["say"], p)
        clips.append((p if p.exists() else p.with_suffix(".aiff"), dur))
    return clips


# --------------------------------------------------------------------------- browser

def run_action(page, a: dict, base: str) -> None:
    k = action_kind(a)
    v = a[k]
    if k == "goto":
        page.goto(urljoin(base, v), wait_until="networkidle")
    elif k == "click":
        page.click(v)
    elif k == "fill":
        page.fill(v, a.get("text", ""))
    elif k == "type":
        page.locator(v).press_sequentially(a.get("text", ""), delay=a.get("delay", 60))
    elif k == "press":
        page.press(a.get("selector", "body"), v)
    elif k == "hover":
        page.hover(v)
    elif k == "scroll":
        page.evaluate("([s, b]) => document.querySelector(s)?.scrollIntoView({behavior: 'smooth', block: b})",
                      [v, a.get("block", "start")])
        page.wait_for_timeout(500)
    elif k == "top":
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.wait_for_timeout(500)
    elif k == "wait":
        page.wait_for_timeout(int(v))
    elif k == "wait_for":
        page.wait_for_selector(v)
    elif k == "eval":
        page.evaluate(v)


def caption(page, text: str) -> None:
    page.evaluate("""([t, css]) => { let c = document.getElementById('demo-cap');
        if (!c) { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
                  c = document.createElement('div'); c.id = 'demo-cap'; document.body.appendChild(c); }
        c.textContent = t; c.style.display = t ? '' : 'none'; }""", [text, CAPTION_CSS])


# --------------------------------------------------------------------------- mux

def ffmpeg_args(video: Path, clips: list[tuple[Path, float]], trim: float, total: float, out: Path) -> list[str]:
    """Cut the video to start at `trim` seconds and lay each clip at its offset (seconds after the cut)."""
    args = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{trim:.3f}", "-i", str(video)]
    for p, _ in clips:
        args += ["-i", str(p)]
    delays = "".join(f"[{i + 1}:a]adelay={int(off * 1000)}|{int(off * 1000)}[a{i}];" for i, (_, off) in enumerate(clips))
    mix = "".join(f"[a{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0[aout]"
    return args + ["-filter_complex", delays + mix, "-map", "0:v", "-map", "[aout]", "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                   "-movflags", "+faststart", "-t", f"{total:.2f}", str(out)]


def record(script: dict, base_dir: Path, frames: bool) -> Path:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH (macOS: brew install ffmpeg; Debian/Ubuntu: apt install ffmpeg)")
    from playwright.sync_api import sync_playwright

    work = Path(tempfile.mkdtemp(prefix="demo-rec-"))
    print("voicing narration ...", flush=True)
    voiced = synthesize(script, work)
    w, h = script["viewport"]
    out = (base_dir / script["output"]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx_args = {"viewport": {"width": w, "height": h}, "record_video_dir": str(work),
                    "record_video_size": {"width": w, "height": h}}
        if script.get("storage_state"):
            ctx_args["storage_state"] = str(base_dir / script["storage_state"])
        ctx = browser.new_context(**ctx_args)
        page = ctx.new_page()
        t_video = time.monotonic()
        page.goto(script["url"], wait_until="networkidle")
        for a in script.get("setup", []):
            run_action(page, a, script["url"])
        page.wait_for_timeout(600)
        t0 = time.monotonic()
        clips = []
        for i, (st, (wav, dur)) in enumerate(zip(script["steps"], voiced), 1):
            start = time.monotonic()
            clips.append((wav, start - t0))
            for a in st.get("actions", []):
                run_action(page, a, script["url"])
            if script["captions"]:
                caption(page, st.get("caption", ""))
            left = dur + script["pad"] - (time.monotonic() - start)
            if left < 0:
                print(f"  step {i}: actions ran {-left:.1f}s past the narration", file=sys.stderr)
            page.wait_for_timeout(max(int(left * 1000), 300))
            print(f"  step {i:2d} at {start - t0:6.1f}s  {st.get('caption') or st['say'][:60]}", flush=True)
        page.wait_for_timeout(int(script["tail_ms"]))
        total = time.monotonic() - t0
        video = Path(page.video.path())
        ctx.close()
        browser.close()

    subprocess.run(ffmpeg_args(video, clips, t0 - t_video, total, out), check=True)
    print(f"\n{out}  ({total:.0f} s)")
    if frames:
        fdir = out.with_name(out.stem + "-frames")
        fdir.mkdir(exist_ok=True)
        for i, (_, off) in enumerate(clips, 1):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{off + 1.2:.2f}", "-i", str(out),
                            "-frames:v", "1", str(fdir / f"step{i:02d}.png")], check=True)
        print(f"frames for review: {fdir}")
    shutil.rmtree(work, ignore_errors=True)
    return out


# --------------------------------------------------------------------------- commands

def cmd_check(script: dict) -> None:
    work = Path(tempfile.mkdtemp(prefix="demo-chk-"))
    voiced = synthesize(script, work)
    total = 0.0
    for i, (st, (_, dur)) in enumerate(zip(script["steps"], voiced), 1):
        seg = dur + script["pad"]
        total += seg
        words = len(st["say"].split())
        print(f"  step {i:2d}  {seg:5.1f}s  {words:3d} words  {st.get('caption', '')}")
    total += script["tail_ms"] / 1000
    print(f"\nestimated length: {int(total // 60)}:{int(total % 60):02d}  ({len(voiced)} steps, voice {script['voice']})")
    shutil.rmtree(work, ignore_errors=True)


def cmd_voices(text: str, out: Path) -> None:
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k = Kokoro(str(MODELS_DIR / "kokoro-v1.0.onnx"), str(MODELS_DIR / "voices-v1.0.bin"))
    out.mkdir(parents=True, exist_ok=True)
    for v in sorted(k.get_voices()):
        if v[:1] not in "ab":  # English voices; pass other prefixes via the script's "voice"
            continue
        audio, sr = k.create(text, voice=v, speed=1.2, lang=LANGS[v[0]])
        sf.write(str(out / f"{v}.wav"), audio, sr)
        print(out / f"{v}.wav")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="install Chromium and download the Kokoro voice model")
    c = sub.add_parser("check", help="validate a script and print its timing")
    c.add_argument("script", type=Path)
    r = sub.add_parser("record", help="record the video")
    r.add_argument("script", type=Path)
    r.add_argument("--frames", action="store_true", help="also save one frame per step for review")
    v = sub.add_parser("voices", help="write a sample WAV per English voice")
    v.add_argument("text")
    v.add_argument("--out", type=Path, default=Path("voice-samples"))
    a = ap.parse_args(argv)

    try:
        if a.cmd == "setup":
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            ensure_models()
            print(f"ready: models in {MODELS_DIR}")
        elif a.cmd == "check":
            cmd_check(load_script(a.script))
        elif a.cmd == "record":
            record(load_script(a.script), a.script.resolve().parent, a.frames)
        elif a.cmd == "voices":
            cmd_voices(a.text, a.out)
    except ScriptError as e:
        raise SystemExit(f"script error: {e}") from e


if __name__ == "__main__":
    main()
