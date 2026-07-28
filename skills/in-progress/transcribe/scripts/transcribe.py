# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mlx-whisper",
#     "av",
#     "numpy",
# ]
# ///
"""Transcribe any audio/video file locally on Apple Silicon.

No system ffmpeg needed: PyAV bundles its own FFmpeg libs and decodes
the audio stream straight to the 16 kHz mono float32 array Whisper expects.
"""
import sys
import time

import av
import numpy as np
import mlx_whisper

SAMPLE_RATE = 16000


def load_audio(path: str) -> np.ndarray:
    container = av.open(path)
    stream = next(s for s in container.streams if s.type == "audio")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    chunks = []
    for frame in container.decode(stream):
        for out in resampler.resample(frame):
            chunks.append(out.to_ndarray().reshape(-1))
    container.close()
    pcm = np.concatenate(chunks)
    return pcm.astype(np.float32) / 32768.0


def main() -> None:
    path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "mlx-community/whisper-base-mlx"

    audio = load_audio(path)
    duration = len(audio) / SAMPLE_RATE
    print(f"audio: {duration:.1f}s, model: {model}", file=sys.stderr)

    t0 = time.time()
    result = mlx_whisper.transcribe(audio, path_or_hf_repo=model)
    elapsed = time.time() - t0
    print(f"transcribed in {elapsed:.1f}s ({duration / elapsed:.1f}x realtime)", file=sys.stderr)

    for seg in result["segments"]:
        print(f"[{seg['start']:7.2f} --> {seg['end']:7.2f}] {seg['text'].strip()}")


if __name__ == "__main__":
    main()
