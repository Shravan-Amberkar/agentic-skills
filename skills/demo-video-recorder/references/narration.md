# Writing the narration

## Shape of a demo

Words scale with length: ~2.6 words per second at speed 1.2, so 30 s ≈ 75 words, 60 s ≈ 150,
2 min ≈ 300, 5 min ≈ 750. The shape below is for the default 2-minute demo (8–10 steps); for a
30–60 s video keep only steps 1, one moment from 3, and 5.

### 2 minutes (8–10 steps, ~300 words)

1. **The problem, for whom** (1 step). "Small brands lose disputes they should win." No feature
   names yet.
2. **The headline result on screen** (1 step). The one number that matters.
3. **Two or three moments of real work** (3–5 steps). Each shows one hard case being handled,
   and why it is hard. This is the part viewers remember.
4. **Trust** (1–2 steps). How you know it is right: checks, tests, an evaluation, a human in the
   loop.
5. **How to use it / what it is built with** (1 step). End on an action the viewer can take.

## Rules that make TTS sound good

- One idea per step, 15–35 words. Long steps leave the screen static; short ones feel choppy.
- Write numbers as they should be spoken: "one and a half lakh", "thirty nine", "two percent".
  Digits and symbols ("₹1.5L", "39/39", "2%") are read oddly or skipped.
- Spell out abbreviations the model may mispronounce: "D to C", "U P I", "A W B".
- Prefer short sentences and full stops over commas and dashes; they produce natural pauses.
- Captions are not the narration: 4–9 words that name the point, symbols are fine there
  ("39 disputes · ₹1.5 lakh at stake").
- Say what the viewer is looking at as it appears ("Here, the customer says…") so the action and
  the voice line up.

## Fitting the length

Set `target_seconds` in the script. `check` prints seconds per step and whether you are on
target, with roughly how many words to cut or add. Cut words before steps; raise `speed` only up
to ~1.25. Being under target is fine — don't pad a short story.
