# Purpose: projects, downloaders, song grouping

**Summary**: Why the next features exist. A musician gets a link to someone else's folder in any layout; Downtempo turns it into songs with their sheets and recordings, kept current. Downloaders only copy files; song grouping (by names) makes the songs; the user fixes the rest by dragging.

Why these parts exist and what "done" means for them. UI plan: [project-screen.md](project-screen.md); grouping logic: [song-grouping.md](song-grouping.md); code blocks: [blocks.md](blocks.md).

## The user's situation

A musician plays in a band, a choir, a folk group or a course. Whoever leads the group keeps the material in a shared cloud folder: sheet music, chords and lyrics as PDFs, reference tracks and rehearsal takes as mp3/wav. The musician doesn't own that folder and can't change how it's organised. Some groups use one folder per song, others one big folder, others folders per rehearsal date, per instrument, per file type. Some songs have only a sheet, some only a recording. Names roughly match ("Harbour Waltz.mp3", "harbour waltz - chords.pdf", "Harbour Waltz 2026-01-15.pdf", "Rehearsal 9.10/harbour waltz 2.wav"), but nobody guarantees it.

What the musician wants: **the group's songs, each with its sheets and recordings, ready to practise, and kept up to date**, without learning how the folder is organised.

## The three parts

**Project** = one group the musician practises with. It holds the places the material comes from, the song list, and the practice memory (tempo, loops). Most users have one; a few have a band and a choir. Everything the user sees in the player belongs to the current project.

**Downloaders** = transport only. They copy the media files from wherever the group keeps them (OneDrive, Google Drive, later something else, or several at once) into the project, and keep the copy current. A downloader answers "which files are there, and what changed". It never decides what a song is.

**Song grouping** = the part that makes the project useful. It turns a pile of files into songs, by **names first** (file and folder names that match or contain the same words), with the folder structure only as a hint. It works the same whatever the folder layout and whichever source a file came from: a sheet from Google Drive and a recording from OneDrive join the same song. It does most of the work automatically, says where it isn't sure, and lets the user fix the rest by **dragging files between songs** in a full-screen view. The user's fixes are remembered and survive updates; new files land in the right song or in a "To sort" tray.

## What "done" looks like

1. Paste a share link, pick the folder, sign in once.
2. The program shows "about 12 songs from 31 files" before downloading.
3. After the download most files sit in the right songs. A few are in "To sort", marked so they're easy to find.
4. Five minutes of dragging, and the project is right. Then practise.
5. Weeks later the leader adds a rehearsal recording. After an update it joins its song, or waits in "To sort" with a badge on the song list.
6. A bandmate gets the project in a settings file, with the sorting already done.

## Not the goal

- Editing, renaming or moving files in the shared folder: the source is read-only for us.
- Perfect automatic grouping. Good guesses, honest about doubt, and quick fixes beat clever rules nobody understands.
- Folder-layout settings for the user to learn. Folder shape is an input to the guesser, not a setting (this replaces the rule-based plan of T53).
- Files other than mp3/wav/pdf (for now).
