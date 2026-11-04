# Recording work or internal apps

What stays local: the browser, the voice model, ffmpeg and the output file. Nothing in this skill
sends page content, narration or video anywhere. The model download (first `setup`) is the only
network call the skill makes.

What you are responsible for is **what appears on screen**:

- Record against a staging/demo environment with synthetic or anonymised data. Real customer
  names, phone numbers, account numbers, emails, amounts tied to people, internal hostnames and
  API keys all end up in every frame.
- Review every `--frames` image before sharing. Also scrub the narration and captions.
- Close dev tools, notifications and tabs; the recording is the page only, but URLs and data in
  the page are captured.
- `storage_state` files contain live session cookies. Keep them out of git, delete after use.
- Check your organisation's policy before posting a video of an internal tool outside the
  company, even if the data is synthetic.
- Do not commit recordings of internal apps to public repositories.
