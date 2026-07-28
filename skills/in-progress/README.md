# In progress

Drafts not yet ready to ship. Nothing here is installed by the plugin, linked by `scripts/link-skills.sh`, or listed in the top-level README.

Planned:

- **compare** — same topic across multiple sources: where they agree, where they contradict, who has the evidence.
- **transcribe** — Whisper fallback for caption-less videos, TikTok, and Instagram Reels. Working prototype landed in [`transcribe/scripts/transcribe.py`](./transcribe/scripts/transcribe.py): PEP 723 uv script, PyAV decodes the media (no system ffmpeg), mlx-whisper transcribes on Apple Silicon (~7x realtime with `whisper-large-v3-turbo` — use it; `base` garbles words too badly for claim extraction). Missing: SKILL.md, non-Apple-Silicon path (faster-whisper), caption-check-first flow.
- **bs-index** — a public website of published BS reports, auto-built from `examples/`. Parked until there's a steady report cadence worth indexing.
