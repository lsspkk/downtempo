# Settings file: share the download settings (plan)

**Summary**: Plan (T66–T69). One TOML text file per project with its sources, skipped folders and sorting (never tokens), sent by email or chat. Import is untrusted: checked, previewed per source, nothing written before the user confirms.

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

- at most 64 KB; a TOML error → "This isn't a Downtempo settings file" plus the line;
- `downtempo` newer than this app knows → "Made by a newer Downtempo; update first";
- links: `https` and owned by a known provider, else that source is refused with the reason;
- names: one safe folder name (no `/`, `\`, `..`, leading dot, control characters; at most 80 characters);
- unknown keys are ignored and listed, never guessed;
- **nothing is written before the user confirms the preview**.

Preview, per source:

| Case | Shown as | Does |
|---|---|---|
| new link | **Add** *my-band* (OneDrive) | adds it |
| same link, same settings | Already here | nothing |
| same link, other sorting | **Update** the sorting (n songs differ) | adds the file's decisions; the importer's own decisions win where both decided, listed |
| name taken by another link | **Add** as *my-band 2* | adds it renamed; its file keys in `[grouping]` are renamed too |

After applying: "Download now?" runs the Downloader UI's progress view.

## API

```python
def export(library: Library, project: str) -> str             # the TOML text
def read(text: str) -> Bundle                                  # checks everything, raises UserError
def preview(library: Library, bundle: Bundle) -> list[Change]  # Add / Same / Update / Rename
def apply(library: Library, changes: list[Change]) -> None
```

CLI: `downtempo export <file>`, `downtempo import <file>` (prints the preview, asks; `--yes` skips the question).

## Player

In the project menu of the [project screen](project-screen.md): **Export…** (save dialog in the native window, a download in `--browser`) and **Copy as text**; **Import…** (open a file) and **Paste**. Both lead to the same preview.

## Projects

Before Projects, import merges into the one library. With projects, an export is one project, and import offers "New project *My band*" or "Add to *current project*".

## Later, if wanted

Ask the user before planning these:

- practice memory (tempo, loops per song): a teacher sending loops to students.
