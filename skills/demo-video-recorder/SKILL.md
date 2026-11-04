---
name: demo-video-recorder
description: Record a narrated demo / walkthrough video of a running web app, fully offline. Writes a step script (narration line + caption + browser actions per step), voices it with the Kokoro neural TTS model (Apache-2.0, runs locally), drives Chromium with Playwright, and muxes an MP4 with ffmpeg where each voice clip starts exactly when its step does. Includes a timing check to hit a target length (e.g. 2 minutes) before recording, and per-step frame capture so the agent can verify what was on screen. Use when asked to "make a demo video", "record a walkthrough / screen recording with voiceover", "2-minute product demo", "narrated video of this app", or to re-record a demo after UI changes. Not for editing existing footage, desktop (non-browser) apps, or cloud TTS voices.
license: MIT
x-spec-version: "1.0"
---

# demo-video-recorder

Turn a running web app into a narrated MP4: a JSON script says what to say and what to do on
screen, and `assets/record.py` does the rest. Everything runs on the user's machine — no cloud
TTS, no upload — so it is safe for internal or work apps as long as what is *on screen* is safe
to show (see [references/privacy.md](references/privacy.md)).

**Locate the bundled script first.** Commands run from the user's project, not from this skill's
directory, so resolve the path once:

```sh
SKILL_DIR="<this skill's base directory>"   # provided by the harness when the skill loads
# otherwise: SKILL_DIR=$(find ~/.claude ~/.codex ~/.agents ~/.cursor -type d -name demo-video-recorder 2>/dev/null | head -1)
REC="$SKILL_DIR/assets/record.py"
```

## Requirements

- `uv` (runs `record.py` with its inline dependencies: kokoro-onnx, soundfile, playwright) and
  `ffmpeg` on PATH (`brew install ffmpeg` / `apt install ffmpeg`).
- One-time: `uv run "$REC" setup` — installs Chromium for Playwright and downloads the Kokoro
  model (~350 MB, checksum-verified) to `~/.cache/demo-video-recorder` (override with
  `DEMO_MODELS_DIR`). Without the model, macOS falls back to `say` (robotic); tell the user.

## Workflow

1. **Frame the video.** Get or infer: the app URL (it must already be running — start it if the
   user asks), the audience (recruiter, customer, internal team), the target length (default 2
   minutes), and the 3–5 things the viewer must remember. If the app needs a login, see
   *Logged-in apps* below.
2. **Find stable selectors.** Read the app's HTML/templates (or open it with Playwright) and pick
   selectors that will not shift: ids, `data-*` attributes, distinctive classes. Note which
   elements need a click before they render (tabs, dialogs, lazy panels).
3. **Write the script** (`demo.json` next to the user's project, or wherever they want the video).
   Format: [references/script-format.md](references/script-format.md). Narration rules:
   [references/narration.md](references/narration.md) — problem first, one idea per step, numbers
   written the way they should be spoken, ~300 words for 2 minutes at speed 1.2.
4. **Check the timing** — `uv run "$REC" check demo.json`. It voices every step (no browser) and
   prints per-step seconds and the estimated length. Trim words until it fits the target; this
   is far cheaper than re-recording.
5. **Record** — `uv run "$REC" record demo.json --frames`. Prints each step's start time and
   writes `<output>.mp4` plus `<output>-frames/stepNN.png` (one frame ~1 s into each step).
6. **Verify before handing over.** Look at every frame: is the thing the narration talks about
   actually visible, caption readable, nothing sensitive on screen? A warning like
   `actions ran 2.1s past the narration` means a step's actions are slower than its line —
   lengthen the line or move actions to the previous step. Fix the script and re-record; never
   hand over a video whose frames you have not checked.
7. **Deliver**: the MP4 path, its length, and the voice used. If the app has a "watch demo"
   link, the MP4 can be served as a static file (≈ 8–10 MB for 2 minutes at 1440×900).

## Logged-in apps

Save a session once, then reference it with `"storage_state"`:

```sh
uv run --with playwright python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=False); c = b.new_context(); pg = c.new_page()
    pg.goto('https://app.example.internal/login'); input('Log in in the browser, then press Enter...')
    c.storage_state(path='auth.json')"
```

`auth.json` holds live session cookies: keep it out of git and delete it after recording. Prefer a
demo/staging account with synthetic data.

## Choosing a voice

Default `am_michael` (US male) at `speed` 1.2 — clear and brisk. `uv run "$REC" voices "Your
sentence here."` writes one WAV per English voice into `voice-samples/` so the user can pick by
ear; British voices start with `b`, US with `a` (e.g. `af_heart`, `bf_emma`, `bm_george`). Kokoro
also ships Hindi, Spanish, French, Italian, Japanese, Portuguese and Mandarin voices — set
`"voice"` to one of them and the language follows the prefix.

## Gotchas

- Smooth scrolling needs time: `scroll` already waits 0.5 s; add `{"wait": 800}` after clicks
  that animate or fetch.
- Long pages: scroll to the element the narration is about, with `"block": "center"` for cards.
- A `<dialog>` or overlay left open covers later steps — close it in the script.
- Stale servers on the same port serve old UI: confirm the URL shows the current build first.
- Captions are injected into the page (`#demo-cap`); set `"captions": false` to record without.
- `eval` runs arbitrary JS in the page — fine for the script author, never for text copied from
  untrusted sources.
