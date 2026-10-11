# Settings file: share the download settings (built)

**Summary**: Core + CLI built (T66, T80, T66.1: `bundle.py`, `bundle_grouping.py`, `downtempo export` / `import`; sources, skipped folders and the sorting); the player's Export… / Import… in the project menu (T67: the text with Copy and Save as file…, paste or open a file, the preview as a new project or into this one, then Download now?); no practice memory in it (T69). One TOML text file per project with its sources, skipped folders and sorting (never tokens), sent by email or chat. Import is untrusted: checked, previewed per source, nothing written before the user confirms.

Idea **Settings file**; part of [blocks.md](blocks.md); tasks in [todo.md](todo.md).

## User picture

A band member set up the project: the shared folders, and sorted the files into songs. A bandmate on another computer wants the same songs. The first one clicks **Export** and emails the file (or pastes the text into a chat); the second clicks **Import**, sees what will be added, clicks **Add and download**, signs in once. No `sources.toml`, no terminal.

## Format

Plain TOML text, so it survives email and chat and can be read before importing. File name `<project>.downtempo.toml`.

```toml
# Downtempo settings. Open Downtempo → Sort songs and sources → project menu → Import.
downtempo = 1                  # format version
project = "My band"
exported = 2026-10-09

[[source]]
name = "my-band"
type = "onedrive"
url = "https://1drv.ms/f/c/..."
folder = "Songs/2026"         # the folder picked inside the share
skip = ["Old"]                 # skipped folders, not downloaded

[grouping]                     # the sorting: song-grouping.md#memory-groupingjson-in-the-project
songs = { harbour-waltz = { title = "Harbour Waltz", also = ["Satamavalssi"], folders = ["my-band:Harbour Waltz"] } }
files = { "my-band:Rehearsal 9.10/take3.wav" = { songs = ["harbour-waltz"], by = "hand", label = "Ending" } }
```

The sorting travels with the sources: paths inside a share are the same on every computer, so the bandmate gets the same songs without sorting again.

**Never in it**: sign-in tokens, `.env`, downloaded files, paths of this computer. A custom OneDrive client ID is included only if this computer uses one other than the built-in one (it identifies the app, it isn't a secret; T54 confirms).

The source part is the same as in `sources.toml` (and later `project.toml`, [projects.md](projects.md)), so export is mostly a copy and import reuses the same checks.

## Import rules

The file comes from someone else, so it's untrusted:

- at most 512 KB (a sorting of 1,000 files is about 100 KB); a TOML error → "This isn't a Downtempo settings file" plus the line;
- `downtempo` newer than this app knows → "Made by a newer Downtempo; update first";
- links: `https` and owned by a known provider, else that source is refused with the reason;
- names: one safe folder name (no `/`, `\`, `..`, leading dot, control characters; at most 80 characters);
- `skip` entries are folder paths inside the source (no `..`, empty parts, control characters), else that source is refused;
- the `[grouping]` table is checked entry by entry, and a bad entry is dropped with a line in the preview, never guessed: song ids are slugs (letters, digits, `-`; at most 80), titles, also-called names and labels printable and at most 120 characters, `by` is `auto` or `hand`, file keys and folder links are `source:path` with a source of this file and a path without `..` or empty parts, a placement naming a song the file doesn't have loses that song (and goes if none is left), at most 5,000 songs and 50,000 files;
- unknown keys are ignored and listed, never guessed;
- **nothing is written before the user confirms the preview**.

Preview, per source:

| Case                       | Shown as                                | Does                                                                                   |
| -------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------- |
| new link                   | **Add** _my-band_ (OneDrive)            | adds it                                                                                |
| same link, same settings   | Already here                            | nothing                                                                                |
| same link, other sorting   | **Update** the sorting (n songs differ) | adds the file's decisions; the importer's own decisions win where both decided, listed |
| name taken by another link | **Add** as _my-band 2_                  | adds it renamed; its file keys and folder links in `[grouping]` are renamed too        |

The sorting is its own line: **Add the sorting** (the project has none), **Update the sorting** (n songs differ, m songs and files added; what stayed yours is listed, five lines, then "…and n more") or "already here". A song of the same id or title (any case) is the same song: it keeps your title, names, folders and placements; new songs and files with no place here are added.

After applying: "Download now?" runs the Downloader UI's progress view.

## API

```python
def export(library: Library, project: str) -> str             # the TOML text
def read(text: str) -> Bundle                                  # checks everything, raises UserError
def preview(library: Library, bundle: Bundle) -> list[Change]  # Add / Same / Update / Rename
def apply(library: Library, changes: list[Change]) -> None
```

Built (T66, T66.1): `export(library)` (sources with `skip`, and `[grouping]` when the project has a sorting), `read(text)` / `read_file(path)` → `Bundle(project, sources, refused, ignored, grouping)`: a bad source is refused with its reason and the rest still import; `preview(library or None, bundle)` → `Change` kinds `add` / `rename` / `same` / `update` (the file's extra and skipped folders are added to ours) and a `SortingChange`; `apply` (sources first, then `library.sorting.replace_memory`, which undo can reverse); the merge, the renaming of source prefixes and the checks are in `bundle_grouping.py`. `extra_folders` travel with their source until grouping replaces them (T90).

CLI: `downtempo export <file>` (`-` prints it), `downtempo import <file> [--new | --add] [--yes]`: prints refused and ignored parts and the preview, asks; `-` reads stdin and needs `--yes`.

## Player

In the project menu of the [project screen](project-screen.md): **Export…** (save dialog in the native window, a download in `--browser`) and **Copy as text**; **Import…** (open a file) and **Paste**. Both lead to the same preview.

## Projects

An export is one project (built, T80). Import offers "New project _My band_" ("My band 2" when taken; it becomes current) or "Add to _current project_" (or `--project P`); with `--yes`, or no projects yet, it's a new project.

## Not now

- Practice memory (tempo, loops per song), e.g. a teacher sending loops to students: asked in T69 (2026-10-11), the user said not now.
