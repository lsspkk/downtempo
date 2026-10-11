"""Turn a file or folder name into the words that name a song, and compare such names.

`clean` is the first stage of song grouping ([docs/song-grouping.md](../../docs/song-grouping.md)):
what is left after dates, brackets, version words, noise words and a trailing key are taken out.
The rest of the module is string work the matching needs: letters, typo tolerance, edit distance,
and the "looks similar" test for one-click suggestions. Pure: no disk, no network.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher

NOISE = frozenset(
    [
        "chords",
        "soinnut",
        "sointu",
        "lyrics",
        "sanat",
        "sheet",
        "notes",
        "nuotit",
        "nuotti",
        "score",
        "partituuri",
        "melody",
        "melodia",
        "demo",
        "live",
        "mix",
        "master",
        "rehearsal",
        "harjoitus",
        "harjoitukset",
        "treeni",
        "part",
        "parts",
        "stemma",
        "voice",
        "ääni",
        "bass",
        "basso",
        "guitar",
        "kitara",
        "fiddle",
        "violin",
        "viulu",
        "accordion",
        "harmonikka",
        "piano",
        "drums",
        "rummut",
        "vocals",
        "laulu",
        "soprano",
        "sopraano",
        "alto",
        "altto",
        "tenor",
        "tenori",
        "pohjat",
        "pohja",
        "taustat",
        "backing",
        "karaoke",
        "instrumental",
    ]
)
TYPES = frozenset(  # folder names that never make a song folder (noise words count too)
    [
        "audio",
        "mp3",
        "wav",
        "pdf",
        "sheets",
        "nuotit",
        "notes",
        "scores",
        "old",
        "vanhat",
        "arkisto",
        "archive",
        "misc",
        "sekalaiset",
        "sekalaista",
        "uudet",
        "new songs",
        "muut",
        "other",
        "set",
        "setti",
        "keikka",
        "gig",
        "recordings",
        "äänitykset",
        "tallenteet",
    ]
)
JUNK = frozenset(  # file names that say nothing
    [
        "scan",
        "img",
        "image",
        "document",
        "untitled",
        "nimetön",
        "new",
        "recording",
        "tallenne",
        "track",
        "audio",
    ]
)
VERSION_WORDS = frozenset({"final", "uusi", "new"})
TAKE_WORDS = frozenset({"take", "otto", "ver", "version", "v"})
VERSION_FORM = re.compile(r"(?:v|ver|version|take|otto)\d+")
# only counts when written with a capital
MUSICAL_KEY = re.compile(r"[A-G][#b]?m?")
SIMILAR = 0.8  # SequenceMatcher ratio of accent-folded keys that counts as "looks like"

SPECIAL = re.compile(
    r"(?P<bracket>[(\[{][^)\]}]*[)\]}])"
    r"|(?P<iso>(?<!\d)\d{4}-\d{2}-\d{2}(?!\d))"
    r"|(?P<compact>(?<!\d)20\d{6}(?!\d))"
    r"|(?P<dmy>(?<![\d.])\d{1,2}\.\d{1,2}(?:\.(?:\d{4}|\d{2}))?(?!\d))"
)
SEPARATORS = re.compile(r"[\s_.\-+,;:]+")
CAMEL = re.compile(r"(?<=[a-zåäö])(?=[A-ZÅÄÖ])")


@dataclass(frozen=True)
class Words:
    noise: frozenset[str] = NOISE
    types: frozenset[str] = TYPES
    junk: frozenset[str] = JUNK


def is_type_name(key: str, words: Words) -> bool:
    """A cleaned folder name made only of type words (`audio`, `uudet`, `new songs`)."""
    return bool(key) and (key in words.types or set(key.split()) <= words.types)


def words_for(add: tuple[str, ...] = (), keep: tuple[str, ...] = ()) -> Words:
    """The built-in words, plus a project's own noise words, minus the ones it treats as real."""
    noise = NOISE | {w.casefold() for w in add}
    return Words(noise=noise - {w.casefold() for w in keep})


@dataclass(frozen=True)
class Cleaned:
    key: str  # "harbour waltz": casefolded words, one space; "" = nothing meaningful
    title: str  # "Harbour Waltz": the same words in their original case
    extras: tuple[str, ...]  # everything taken out, in order of appearance
    tags: tuple[
        str, ...
    ]  # extras that are not dates, numbers or versions: they make a sheet its own
    date: date | None  # the first full date found
    version: bool  # had a version or take word


def clean(name: str, words: Words) -> Cleaned:
    """`clean("Harbour_Waltz - CHORDS 2026-01-15")` → key `harbour waltz`, extras `CHORDS`,
    `2026-01-15`. `name` has no file ending."""
    text = unicodedata.normalize("NFC", name)
    # [kind, text]; kind: word, tag, date, number, version
    items: list[list[str]] = []
    found: date | None = None
    position = 0
    for match in SPECIAL.finditer(text):
        ok, when = read_special(match)
        if not ok:
            continue
        add_words(items, text[position : match.start()])
        inner = match.group()
        if match.lastgroup == "bracket":
            inner = inner[1:-1].strip()
            kind = "tag"
        else:
            kind = "date"
        if inner:
            items.append([kind, inner])
        found = found or when
        position = match.end()
    add_words(items, text[position:])
    version = mark_anywhere(items, words)
    version = strip_trailing(items) or version
    kept = [text for kind, text in items if kind == "word"]
    if all(w.casefold().rstrip("0123456789") in words.junk for w in kept):
        kept = []
    key = unicodedata.normalize(
        "NFC", " ".join("and" if w == "&" else w.casefold() for w in kept)
    )
    return Cleaned(
        key=key,
        title=" ".join(kept),
        extras=tuple(text for kind, text in items if kind != "word"),
        tags=tuple(text for kind, text in items if kind == "tag"),
        date=found,
        version=version,
    )


def read_special(match: re.Match[str]) -> tuple[bool, date | None]:
    """Whether a bracket or date-like text really is one, and the date it names."""
    kind, text = match.lastgroup, match.group()
    try:
        match kind:
            case "bracket":
                return True, None
            case "iso":
                return True, date.fromisoformat(text)
            case "compact":
                return True, date(int(text[:4]), int(text[4:6]), int(text[6:]))
            case _:
                parts = [int(p) for p in text.split(".")]
                year = parts[2] if len(parts) > 2 else None
                if year is not None and year < 100:
                    year += 2000
                when = date(year or 2000, parts[1], parts[0])
                return True, when if year else None
    except ValueError:
        return False, None


def add_words(items: list[list[str]], text: str) -> None:
    for raw in SEPARATORS.split(text):
        raw = raw.strip("'\"!?")
        if not raw:
            continue
        for word in CAMEL.split(raw) if raw.isalpha() else [raw]:
            items.append(["word", word])


def mark_anywhere(items: list[list[str]], words: Words) -> bool:
    """Noise words and `v2` / `take 2` forms, wherever they are."""
    version = False
    for i, (kind, text) in enumerate(items):
        if kind != "word":
            continue
        folded = text.casefold()
        following = items[i + 1] if i + 1 < len(items) else None
        if folded in words.noise:
            items[i][0] = "tag"
        elif VERSION_FORM.fullmatch(folded):
            items[i][0], version = "version", True
        elif (
            folded in TAKE_WORDS
            and following
            and following[0] == "word"
            and following[1].isdigit()
        ):
            items[i][0] = following[0] = "version"
            version = True
    return version


def strip_trailing(items: list[list[str]]) -> bool:
    """From the end: a number, `final` / `uusi` / `new`, a capital musical key (and its `in`)."""
    version = False
    while True:
        indexes = [i for i, (kind, _) in enumerate(items) if kind == "word"]
        if not indexes:
            return version
        last = indexes[-1]
        text = items[last][1]
        folded = text.casefold()
        if text.isdigit():
            items[last][0] = "number"
        elif len(indexes) > 1 and folded in VERSION_WORDS:
            items[last][0], version = "version", True
        elif len(indexes) > 1 and MUSICAL_KEY.fullmatch(text):
            items[last][0] = "tag"
            before = indexes[-2]
            if len(indexes) > 2 and items[before][1].casefold() == "in":
                items[before][0] = "tag"
        else:
            return version


def letters(key: str) -> str:
    return key.replace(" ", "")


def tolerance(letter_count: int) -> int:
    """How many letters may differ: 0 under 5 letters, 1 from 5, 2 from 10."""
    return 0 if letter_count < 5 else 1 if letter_count < 10 else 2


def edit_distance(a: str, b: str, limit: int) -> int:
    """Levenshtein distance, or `limit + 1` when it is more than `limit`."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        if min(current) > limit:
            return limit + 1
        previous = current
    return min(previous[-1], limit + 1)


def fold(key: str) -> str:
    """Without accents (`ä` → `a`): only for "looks like", never for joining a song."""
    decomposed = unicodedata.normalize("NFKD", key)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def similar(a: str, b: str) -> bool:
    """Two keys that read alike beyond the typo tolerance: the same words in any order, or a
    close letter-by-letter match."""
    a, b = fold(a), fold(b)
    if not a or not b:
        return False
    if sorted(a.split()) == sorted(b.split()):
        return True
    return SequenceMatcher(None, a, b, autojunk=False).ratio() >= SIMILAR
