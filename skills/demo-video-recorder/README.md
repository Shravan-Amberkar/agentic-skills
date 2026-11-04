# demo-video-recorder (Agent Skill)

Record a **narrated demo video of any running web app**, entirely offline. You (or your agent)
write a short JSON script — what to say and what to click per step — and get an MP4 with a
natural neural voiceover, on-screen captions, and audio that lines up with the screen.

- **Voice:** [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) (Apache-2.0), runs on your
  CPU. No cloud TTS, no account, no upload.
- **Browser:** Playwright + Chromium, any viewport.
- **Mux:** ffmpeg places each narration clip at the moment its step starts.
- **Fit the length first:** `check` voices the script and prints the timing before you record.
- **Verify:** `--frames` saves one frame per step so you (or the agent) can check what was on
  screen.

## Install

```bash
npx skills add Shravan-Amberkar/demo-video-recorder
# or copy skills/demo-video-recorder into your agent's skills folder (e.g. ~/.claude/skills/)
```

Needs [`uv`](https://docs.astral.sh/uv/) and `ffmpeg`. Then once:

```bash
uv run skills/demo-video-recorder/assets/record.py setup   # Chromium + voice model (~350 MB)
```

## Use

Ask your agent: *"Make a 2-minute demo video of the app on localhost:3000 for a recruiter."* It
writes the script, checks the timing, records, and reviews the frames. Or by hand:

```bash
REC=skills/demo-video-recorder/assets/record.py
uv run $REC check  demo.json            # per-step seconds + total length, no browser
uv run $REC record demo.json --frames   # -> demo.mp4 + demo-frames/stepNN.png
uv run $REC voices "Try this sentence." # sample every English voice
```

A minimal script:

```json
{
  "url": "http://127.0.0.1:3000/",
  "output": "demo.mp4",
  "steps": [
    {"say": "Finance teams lose a day every month matching bank credits by hand.",
     "caption": "The month-end problem", "actions": [{"top": true}]},
    {"say": "Here, every payment is matched and proven, with the rule that matched it.",
     "caption": "Every match comes with proof", "actions": [{"click": "[data-tab=paid]"}, {"wait": 600}]}
  ]
}
```

Full format: [references/script-format.md](references/script-format.md) · Narration tips:
[references/narration.md](references/narration.md) · Recording work apps:
[references/privacy.md](references/privacy.md).

## Tests

```bash
python3 -m unittest discover -s skills/demo-video-recorder/assets -p 'test_*.py'
```
