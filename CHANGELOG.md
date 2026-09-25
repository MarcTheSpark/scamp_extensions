# Changelog

All notable user-facing changes to scamp_extensions are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-09-25

### Added

- **`MultiPresetInstrument` and `MultiStaffInstrument` pass `fixed` and `velocity` through
  `start_note`/`start_chord`**, matching scamp's new per-note fixedness control and independent note-on velocity.

### Changed

- **`MultiPresetInstrument`/`MultiStaffInstrument`'s `start_note`/`start_chord` `max_volume` argument is replaced
  by `velocity`**, following the same change in scamp. If you passed `max_volume=x`, pass `velocity=x`.
- **`utilities.math.remap()` of a single value now accepts an omitted input range**, defaulting to `[0, 1]` when
  neither `in_min` nor `in_max` is given (previously it required both).

### Removed

- **The `scamp_extensions.playback.supercollider` subpackage is removed** (`SCPlaybackImplementation`,
  `SCLangInstance`, `add_sc_extensions`). This functionality relied on monkey-patching the Ensemble object, and
  starting up SuperCollider as a subprocess, which was finicky. Instead, talk to SuperCollider over OSC, using
  the [SCScampUtils](https://github.com/MarcTheSpark/SCScampUtils) quark for convenience on the SuperCollider side.

### Fixed

- **`PartNoteGraph.render_to_file()` works with current `drawsvg`.** It called the library's old
  camelCase methods (`addStop`, `setPixelScale`, `saveSvg`), which were renamed to snake_case, and
  drew the graph upside down under drawsvg 2.x's downward y-axis.
- **`TimeVaryingParameter` works again.** It broke when the clock's position accessors became properties,
  and has now been adapted to read them as such.

## [0.3.7] - 2026-07-12

### Changed

- **Requires the scamp 1.0-era dependencies**: `scamp>=0.10.0`, `clockblocks>=1.0.0`,
  `expenvelope>=0.8.0`. scamp_extensions' own API is unchanged, but code that uses it
  inherits clockblocks 1.0's breaking changes — most notably that forked functions no
  longer receive the clock as an argument, and that tempo targets take a `Moment`. See the
  [clockblocks 1.0 changelog](https://github.com/MarcTheSpark/clockblocks/blob/main/CHANGELOG.md).
- **`drawsvg` is now an optional dependency.** It is imported lazily by the engraving
  extension, so scamp_extensions installs and imports without it. If you use
  `engraving.note_graph`, install it with `pip install scamp_extensions[engraving]`.
- Docstrings added across the public API.

### Fixed

- Silenced `SyntaxWarning: invalid escape sequence` emitted on import of the bundled
  `process._pykov` module under Python 3.12+ — its LaTeX-in-docstrings are now raw strings.

## Earlier versions

For changes prior to 0.3.7, see the commit history.
