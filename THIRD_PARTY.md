# Third-party material

The `gold.patch` and `test.patch` files under `tasks/` are excerpts of the upstream projects below: diffs of changes
contributed to those projects, with a few lines of the surrounding upstream code as context. Each file stays under the
license of the project it comes from. Everything else in this repository (the harness, `task.json`, `problem.md`, the
`check_*` scripts, `tools/` and the tests written for this benchmark) is under the MIT License in [LICENSE](LICENSE).

| Project | License | Tasks |
|---|---|---|
| [bombshell-dev/clack](https://github.com/bombshell-dev/clack) | [MIT](https://github.com/bombshell-dev/clack/blob/main/LICENSE) | `clack-627` |
| [BYVoid/OpenCC](https://github.com/BYVoid/OpenCC) | [Apache-2.0](https://github.com/BYVoid/OpenCC/blob/master/LICENSE) | `opencc-1509`, `opencc-1510`, `opencc-1511`, `opencc-1512`, `opencc-1514` |
| [charmbracelet/glamour](https://github.com/charmbracelet/glamour) | [MIT](https://github.com/charmbracelet/glamour/blob/main/LICENSE) | `glamour-651` |
| [dbcli/mycli](https://github.com/dbcli/mycli) | [BSD-3-Clause](https://github.com/dbcli/mycli/blob/main/LICENSE.txt) | `mycli-2389` |
| [foliojs/pdfkit](https://github.com/foliojs/pdfkit) | [MIT](https://github.com/foliojs/pdfkit/blob/master/LICENSE) | `pdfkit-1828` |
| [FullHuman/purgecss](https://github.com/FullHuman/purgecss) | [MIT](https://github.com/FullHuman/purgecss/blob/main/LICENSE) | `purgecss-1505` |
| [fuma-nama/fumadocs](https://github.com/fuma-nama/fumadocs) | [MIT](https://github.com/fuma-nama/fumadocs/blob/dev/LICENSE) | `fumadocs-3752` |
| [kevin1024/vcrpy](https://github.com/kevin1024/vcrpy) | [MIT](https://github.com/kevin1024/vcrpy/blob/master/LICENSE.txt) | `vcrpy-1066` |
| [lsd-rs/lsd](https://github.com/lsd-rs/lsd) | [Apache-2.0](https://github.com/lsd-rs/lsd/blob/main/LICENSE) | `lsd-1248` |
| [orhun/git-cliff](https://github.com/orhun/git-cliff) | [Apache-2.0 OR MIT](https://github.com/orhun/git-cliff/blob/main/LICENSE-MIT) | `git-cliff-1657` |
| [plotly/dash](https://github.com/plotly/dash) | [MIT](https://github.com/plotly/dash/blob/dev/LICENSE) | `dash-4074` |
| [PyCQA/isort](https://github.com/PyCQA/isort) | [MIT](https://github.com/PyCQA/isort/blob/main/LICENSE) | `isort-2744` |
| [rany2/edge-tts](https://github.com/rany2/edge-tts) | [LGPL-3.0](https://github.com/rany2/edge-tts/blob/master/LICENSE) | `edge-tts-506` |
| [wanasit/chrono](https://github.com/wanasit/chrono) | [MIT](https://github.com/wanasit/chrono/blob/master/LICENSE.txt) | `chrono-682` |
| [Y2Z/monolith](https://github.com/Y2Z/monolith) | [CC0-1.0](https://github.com/Y2Z/monolith/blob/master/LICENSE) | `monolith-541` |

`edge-tts` is licensed under the LGPL-3.0, except `src/edge_tts/srt_composer.py` (MIT); the `edge-tts-506` gold patch
changes `src/edge_tts/communicate.py`, which is LGPL-3.0. `git-cliff` is dual-licensed under Apache-2.0 and MIT.

No upstream repository is copied here: the harness clones each one from GitHub at run time.
