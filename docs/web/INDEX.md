# Saved web pages

Read the `.txt` copy, not the `.html` (the raw HTML is the original, kept for reference).
Add pages only through `scripts/webfetch.py`, which appends one row here.

| name | saved | url | summary |
|---|---|---|---|
| entra-register-app | 2026-10-08 | https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app | Register an app in Entra; supported account types (Personal accounts only) |
| entra-device-code-flow | 2026-10-08 | https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code | OAuth device code flow; /common, /consumers, /organizations authorities |
| msal-python-acquire-token | 2026-10-08 | https://learn.microsoft.com/en-us/entra/msal/python/getting-started/acquiring-tokens | MSAL Python: acquire_token_silent, device flow |
| msal-python-token-cache | 2026-10-08 | https://learn.microsoft.com/en-us/entra/msal/python/advanced/msal-python-token-cache-serialization | MSAL Python: SerializableTokenCache to persist sign-in |
| msal-python-device-flow-sample | 2026-10-08 | https://raw.githubusercontent.com/AzureAD/microsoft-authentication-library-for-python/dev/sample/device_flow_sample.py | Official MSAL device flow sample code |
| graph-onedrive-overview | 2026-10-08 | https://learn.microsoft.com/en-us/graph/onedrive-concept-overview | Graph OneDrive concepts: drives, driveItems |
| graph-shares-get | 2026-10-08 | https://learn.microsoft.com/en-us/graph/api/shares-get?view=graph-rest-1.0 | GET /shares/{u!..}/driveItem; Prefer: redeemSharingLink; needs Files.ReadWrite (personal) |
| graph-driveitem-list-children | 2026-10-08 | https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0 | List folder children, paging; Files.Read |
| graph-driveitem-get-content | 2026-10-08 | https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0 | Download: 302 to preauthenticated downloadUrl, no auth header |
| graph-permissions-files | 2026-10-08 | https://learn.microsoft.com/en-us/graph/permissions-reference | Graph permissions reference (Files.*) |
| msqa-2138092-shares-api-behavior | 2026-10-08 | https://learn.microsoft.com/en-us/answers/questions/2138092/onedrive-shares-api-behavior-no-longer-reflects-do | api.onedrive.com anonymous shares now 400/401 (Vroom exception) |
| msqa-2130053-direct-link-conversion | 2026-10-08 | https://learn.microsoft.com/en-us/answers/questions/2130053/issues-with-onedrive-direct-link-conversion | Direct-link conversion broke; badger token workaround |
| msqa-1195727-anonymous-graph | 2026-10-08 | https://learn.microsoft.com/en-us/answers/questions/1195727/anonymously-read-and-upload-to-publicly-shared-one | Anonymous Graph access to shared folder not supported |
| msqa-5011486-anonymous-js | 2026-10-08 | https://learn.microsoft.com/en-my/answers/questions/5011486/how-can-i-anonymously-access-no-login-a-publicly-s | Anonymous JS access to public folder: not supported |
| github-onedrive-api-docs-1555 | 2026-10-08 | https://github.com/OneDrive/onedrive-api-docs/issues/1555 | Auth issue for anonymous shared drives |
| dajbych-public-folders-discontinued | 2026-10-08 | https://www.dajbych.net/public-folders-suddenly-discontinued-in-personal-onedrive | Public folders discontinued in personal OneDrive |
| codez-one-badger-api | 2026-10-08 | https://www.codez.one/onedrive-share-links-und-die-versteckte-badger-api-eine-langjahrige-odyssee/ | (German) reverse-engineered Badger token API; rejected approach |
| pylibrb-readme | 2026-10-08 | https://raw.githubusercontent.com/pawel-glomski/pylibrb/main/README.md | pylibrb README: nanobind Rubber Band binding, realtime + offline, numpy API |
| python-stretch-readme | 2026-10-08 | https://raw.githubusercontent.com/gregogiudici/python-stretch/main/README.md | python-stretch README: Signalsmith Stretch wrapper, numpy, time factor + transpose |
| signalsmith-stretch-readme | 2026-10-08 | https://raw.githubusercontent.com/Signalsmith-Audio/signalsmith-stretch/main/README.md | Signalsmith Stretch C++ README: MIT, streaming API, quality notes |
| pytimestretch-readme | 2026-10-08 | https://raw.githubusercontent.com/openmirlab/pytimestretch/main/README.md | pytimestretch: one interface for Rubber Band + Signalsmith, early, not on PyPI |
| rubberband-stretcher-class | 2026-10-08 | https://breakfastquay.com/rubberband/code-doc/classRubberBand_1_1RubberBandStretcher.html | Rubber Band RubberBandStretcher API: realtime mode, process/retrieve, setTimeRatio live, R3 engine |
| pedalboard-readme | 2026-10-08 | https://raw.githubusercontent.com/spotify/pedalboard/master/README.md | pedalboard README: AudioFile mp3 decode, AudioStream live output, GPLv3 |
| pedalboard-api-reference | 2026-10-08 | https://spotify.github.io/pedalboard/reference/pedalboard.html | pedalboard API: time_stretch (offline buffer, Rubber Band), AudioStream, AudioFile |
| pyrubberband-docs | 2026-10-08 | https://pyrubberband.readthedocs.io/en/stable/ | pyrubberband: calls rubberband CLI via temp files, offline only |
| lwn-pedalboard | 2026-10-08 | https://lwn.net/Articles/1027814/ | LWN article on pedalboard (2025): features incl. AudioStream |
| pypi-pylibrb-json | 2026-10-08 | https://pypi.org/pypi/pylibrb/json | PyPI JSON metadata for pylibrb: versions, release dates, wheel files, license |
| pypi-python-stretch-json | 2026-10-08 | https://pypi.org/pypi/python-stretch/json | PyPI JSON metadata for python-stretch: versions, release dates, wheel files, license |
| pypi-pedalboard-json | 2026-10-08 | https://pypi.org/pypi/pedalboard/json | PyPI JSON metadata for pedalboard: versions, release dates, wheel files, license |
| pypi-pyrubberband-json | 2026-10-08 | https://pypi.org/pypi/pyrubberband/json | PyPI JSON metadata for pyrubberband: versions, release dates, wheel files, license |
| pypi-audiotsm-json | 2026-10-08 | https://pypi.org/pypi/audiotsm/json | PyPI JSON metadata for audiotsm: versions, release dates, wheel files, license |
| pypi-librosa-json | 2026-10-08 | https://pypi.org/pypi/librosa/json | PyPI JSON metadata for librosa: versions, release dates, wheel files, license |
| pypi-sounddevice-json | 2026-10-08 | https://pypi.org/pypi/sounddevice/json | PyPI JSON metadata for sounddevice: versions, release dates, wheel files, license |
| pypi-soundfile-json | 2026-10-08 | https://pypi.org/pypi/soundfile/json | PyPI JSON metadata for soundfile: versions, release dates, wheel files, license |
| pypi-nicegui-json | 2026-10-08 | https://pypi.org/pypi/nicegui/json | PyPI JSON metadata for nicegui: versions, release dates, wheel files, license |
| pypi-pytsmod-json | 2026-10-08 | https://pypi.org/pypi/pytsmod/json | PyPI JSON metadata for pytsmod: versions, release dates, wheel files, license |
| pywebview-installation | 2026-10-08 | https://pywebview.flowrl.com/guide/installation.html | pywebview installation: Linux needs GTK (PyGObject) or QT (qtpy + PyQt/PySide) backend |
| nicegui-native-mode | 2026-10-08 | https://raw.githubusercontent.com/zauberzeug/nicegui/main/website/documentation/content/section_configuration_deployment.py | NiceGUI docs source, configuration & deployment: native mode (ui.run(native=True), pywebview, window_size, app.native) |
| design-transcribe-overview | 2026-10-08 | https://www.seventhstring.com/xscribe/overview.html | Transcribe! overview: music practice app features (loops, markers, speed, waveform) |
| design-anytune | 2026-10-08 | https://www.anytune.app/ | Anytune: practice app features (slow down, loop, step-up trainer, marks) |
| design-nng-heuristics | 2026-10-08 | https://www.nngroup.com/articles/ten-usability-heuristics/ | NN/g 10 usability heuristics |
| design-youtube-shortcuts | 2026-10-08 | https://support.google.com/youtube/answer/7631406?hl=en | YouTube keyboard shortcuts: media player key conventions |
| design-nng-sliders | 2026-10-08 | https://www.nngroup.com/articles/gui-slider-controls/ | NN/g slider design: when sliders fit, precise input, labels, steps |
| wiki-audio-time-stretching | 2026-10-08 | https://en.wikipedia.org/wiki/Audio_time_stretching_and_pitch_scaling | Wikipedia: time stretching and pitch scaling; resampling, phase vocoder, time-domain (SOLA/WSOLA), artifacts |
| wiki-phase-vocoder | 2026-10-08 | https://en.wikipedia.org/wiki/Phase_vocoder | Wikipedia: phase vocoder; STFT, phase coherence, phasiness, phase locking |
| rubberband-technical | 2026-10-08 | https://breakfastquay.com/rubberband/technical.html | Rubber Band technical notes: how R2/R3 engines work, phase vocoder with transient handling |
| rubberband-home | 2026-10-08 | https://breakfastquay.com/rubberband/ | Rubber Band Library home: features, R3 finer engine, license (GPL/commercial) |
| soundtouch-readme | 2026-10-08 | https://www.surina.net/soundtouch/README.html | SoundTouch README: WSOLA-based tempo change, sequence/seek window parameters, LGPL |
| bungee-readme | 2026-10-08 | https://raw.githubusercontent.com/bungee-audio-stretch/bungee/main/README.md | Bungee README: modern open-source real-time time stretch, MPL-2.0, frequency-domain with grains |
| rubberband-integration | 2026-10-08 | https://breakfastquay.com/rubberband/integration.html | Rubber Band integration advice: R2 vs R3 engines, real-time vs offline, latency, CPU, options |
| djay-tempo-per-song | 2026-10-08 | https://community.algoriddim.com/t/tempo-settings-persistence-per-song/15397 | djay community request: tempo settings should persist per song (practice use) |
| anytune-basics | 2026-10-08 | https://de.anytune.us/user-guide/basics | Anytune user guide basics: per-song tempo/pitch saved, next/previous song navigation, playlists |
| bungee-compare | 2026-10-08 | https://bungee.parabolaresearch.com/compare-audio-stretch-tempo-pitch-change.html | Bungee comparison page: listening comparison of time-stretch libraries (Bungee, Rubber Band, SoundTouch, ...) |
| mdn-preservespitch | 2026-10-08 | https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/preservesPitch | MDN HTMLMediaElement.preservesPitch: pitch kept when playbackRate changes, browser support |
| mdn-playbackrate | 2026-10-08 | https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/playbackRate | MDN HTMLMediaElement.playbackRate: range, muted outside 0.25-4 in some browsers |
| chromium-audio-renderer-algorithm | 2026-10-08 | https://raw.githubusercontent.com/chromium/chromium/main/media/filters/audio_renderer_algorithm.h | Chromium media/filters/audio_renderer_algorithm.h: WSOLA used for playbackRate with pitch kept |
| soundtouchjs-readme | 2026-10-08 | https://raw.githubusercontent.com/cutterbl/SoundTouchJS/master/README.md | SoundTouchJS README: JS port of SoundTouch for Web Audio, PitchShifter, licence |
| rubberband-web-readme | 2026-10-08 | https://raw.githubusercontent.com/delude88/rubberband-web/main/README.md | rubberband-web README: Rubber Band compiled to WASM as an AudioWorklet (realtime) for the browser |
| gecko-audiostream | 2026-10-08 | https://raw.githubusercontent.com/mozilla/gecko-dev/master/dom/media/AudioStream.cpp | Firefox dom/media/AudioStream.cpp: playbackRate with pitch kept uses SoundTouch (time-domain WSOLA-style) |
| rubberband-v3-announcement | 2026-10-08 | https://breakfastquay.com/news/20220707.html | Rubber Band v3.0 announcement: new R3 (finer) engine, what it improves, CPU cost |
| rubberband-v4-announcement | 2026-10-08 | https://breakfastquay.com/news/20241025.html | Rubber Band v4.0 announcement: simplified pitch-shifting API, changes |
| signalsmith-stretch-npm-readme | 2026-10-08 | https://unpkg.com/signalsmith-stretch/README.md | Signalsmith Stretch npm package README: Web Audio (WASM AudioWorklet) node, API, live rate/pitch |
| nng-hamburger-menus | 2026-10-09 | https://www.nngroup.com/articles/hamburger-menus/ | NN/g: hamburger menus hide navigation, lower discoverability; visible labels work better |
| nng-icon-usability | 2026-10-09 | https://www.nngroup.com/articles/icon-usability/ | NN/g icon usability: few icons are universal, icons need text labels, the hamburger means menu |
| forscore-basics | 2026-10-09 | https://forscore.co/documentation/basics/ | forScore 15 user guide, Basics: main toolbar icons (score menu, bookmarks, setlists, tools), title, page turns, half-page turns |
| forscore-menus | 2026-10-09 | https://forscore.co/documentation/menus/ | forScore 15 user guide, Menus: library panels (scores, bookmarks, setlists) opened from labelled toolbar icons, sorting, search |
| forscore-audio | 2026-10-09 | https://forscore.co/documentation/audio/ | forScore 15 user guide, Audio: tracks linked to a score, the compact player in the title bar, switching tracks, loops and rate |
| audacity-zooming | 2026-10-10 | https://manual.audacityteam.org/man/zooming.html | Audacity manual: zooming (Ctrl+wheel, zoom to selection, fit to width, zoom toggle) |
| audacity-timeline | 2026-10-10 | https://manual.audacityteam.org/man/timeline.html | Audacity manual: timeline (ruler) click to play/seek, Quick-Play, looping region on the ruler |
| peaksjs-readme | 2026-10-10 | https://raw.githubusercontent.com/bbc/peaks.js/master/README.md | BBC peaks.js README: zoomview + overview waveform, segments, points, zoom levels, waveform data precomputed |
| wavesurfer-regions-example | 2026-10-10 | https://raw.githubusercontent.com/katspaugh/wavesurfer.js/main/examples/regions.js | wavesurfer.js regions example: drag to create, resize handles, loop region |
| audacity-selecting-audio | 2026-10-10 | https://manual.audacityteam.org/man/audacity_selection.html | Audacity manual: making and adjusting selections (click/drag, Shift-click, edges, snapping) |
| tomlkit-quickstart | 2026-10-10 | https://tomlkit.readthedocs.io/en/latest/quickstart/ | tomlkit quickstart: parse/dumps keep comments, whitespace and order; document behaves like a dict; add tables/comments |
| pypi-tomlkit-json | 2026-10-10 | https://pypi.org/pypi/tomlkit/json | PyPI JSON metadata for tomlkit: versions, release dates, licence |
| msal-python-api | 2026-10-10 | https://msal-python.readthedocs.io/en/latest/ | MSAL Python API reference: PublicClientApplication, initiate_device_flow, acquire_token_by_device_flow(exit_condition), token cache |
| entra-public-confidential-clients | 2026-10-10 | https://learn.microsoft.com/en-us/entra/identity-platform/msal-client-applications | Microsoft: public vs confidential client apps; public clients can't keep secrets, client ID is not a secret |
| nicegui-run-io-bound | 2026-10-10 | https://raw.githubusercontent.com/zauberzeug/nicegui/main/website/documentation/content/section_action_events.py | NiceGUI docs source, action & events: ui.timer, run.io_bound / run.cpu_bound, background_tasks, async handlers |
| nicegui-background-tasks-src | 2026-10-10 | https://raw.githubusercontent.com/zauberzeug/nicegui/main/nicegui/background_tasks.py | NiceGUI background_tasks.py source: create, create_lazy, await_on_shutdown |
| tomlkit-api | 2026-10-11 | https://tomlkit.readthedocs.io/en/latest/api/ | tomlkit API reference: parse, dumps, document, table, aot (array of tables), comment, nl, item types |
