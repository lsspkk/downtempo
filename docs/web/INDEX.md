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
