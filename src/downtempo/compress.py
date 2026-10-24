"""Downloaded wav recordings are kept as mp3: practice needs no hi-fi, and wav takes ~10x the space
(the requirements: docs/compress.md).

`stored_as` says where a downloaded file lives on disk; `to_mp3` encodes one wav. Quality and the
on/off switch are constants in `config.py`. soundfile (libsndfile) writes the mp3, no ffmpeg.
"""

import threading
from pathlib import Path

import soundfile as sf

from downtempo.config import COMPRESS_WAV, MP3_QUALITY
from downtempo.errors import Cancelled

BLOCK = 1 << 16  # frames per read; a cancel is noticed once per block


def stored_as(local: Path, listed: set[Path]) -> Path:
    """`Song.wav` is stored as `Song.mp3`, unless the server also has a `Song.mp3` there."""
    if not COMPRESS_WAV or local.suffix.lower() != ".wav":
        return local
    mp3 = local.with_suffix(".mp3")
    return local if mp3 in listed else mp3


def to_mp3(wav: Path, mp3: Path, cancel: threading.Event) -> bool:
    """Encode `wav` into `mp3` (written whole or not at all); False when libsndfile can't read or
    encode it. The wav is left for the caller."""
    partial = mp3.with_name(mp3.name + ".part")
    try:
        with (
            sf.SoundFile(wav) as source,
            sf.SoundFile(
                partial,
                "w",
                source.samplerate,
                source.channels,
                subtype="MPEG_LAYER_III",
                format="MP3",
                compression_level=MP3_QUALITY,
            ) as output,
        ):
            for block in source.blocks(BLOCK, dtype="float32", always_2d=True):
                if cancel.is_set():
                    raise Cancelled()
                output.write(block)
    except sf.LibsndfileError:
        partial.unlink(missing_ok=True)
        return False
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    partial.replace(mp3)
    return True
