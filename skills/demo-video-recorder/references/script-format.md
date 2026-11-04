# Demo script format

A JSON object. Keys starting with `_` are notes and ignored; any other unknown key is an error.

| Key | Default | Meaning |
|---|---|---|
| `url` | required | The running app (http/https). Relative `goto` targets resolve against it. |
| `output` | `demo.mp4` | Output path, relative to the script file. |
| `viewport` | `[1440, 900]` | Browser size = video size. |
| `voice` | `am_michael` | Kokoro voice id, or `"say"` for the macOS voice. |
| `lang` | from voice prefix | espeak language (`en-us`, `en-gb`, `hi`, …). Rarely needed. |
| `speed` | `1.2` | Speech rate. 1.1–1.25 sounds natural for demos. |
| `pad` | `0.35` | Seconds of silence after each narration line. |
| `tail_ms` | `800` | Hold on the last frame. |
| `captions` | `true` | Show each step's caption at the bottom of the page. |
| `storage_state` | none | Playwright session file for logged-in apps (relative to the script). |
| `setup` | `[]` | Actions run after load and **cut from the video** (dismiss banners, pick a tenant). |
| `steps` | required | List of steps, below. |

## Step

```json
{"say": "Narration spoken during this step.",
 "caption": "Short on-screen text (optional, ≤ 60 chars)",
 "actions": [{"click": "[data-tab=reports]"}, {"wait": 600}, {"scroll": "#chart", "block": "center"}]}
```

The narration starts when the step starts; the actions run immediately; the step lasts as long
as its narration plus `pad`.

## Actions

Each action is an object with exactly one action key.

| Action | Example | Notes |
|---|---|---|
| `goto` | `{"goto": "/settings"}` | Navigates and waits for network idle. |
| `click` | `{"click": "#run"}` | |
| `fill` | `{"fill": "#q", "text": "acme"}` | Instant. |
| `type` | `{"type": "#q", "text": "acme", "delay": 60}` | Visible typing. |
| `press` | `{"press": "Enter", "selector": "#q"}` | Selector defaults to `body`. |
| `hover` | `{"hover": ".row:first-child"}` | |
| `scroll` | `{"scroll": "#kpis", "block": "center"}` | Smooth; `block` = start / center / end. |
| `top` | `{"top": true}` | Smooth scroll to the top. |
| `wait` | `{"wait": 800}` | Milliseconds. |
| `wait_for` | `{"wait_for": ".result"}` | Until the selector appears. |
| `eval` | `{"eval": "select('case-12')"}` | JS in the page, for app-specific helpers. |

## Example

See [`../assets/example-script.json`](../assets/example-script.json).
