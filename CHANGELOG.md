# Changelog

> These changelogs are AI-written and human-reviewed, because no one (least of all my wife
> and kids) wants me wasting my precious time meticulously documenting this shit, useful
> though it may be.

All notable user-facing changes to scamp_extensions are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## Earlier versions

For changes prior to 0.3.7, see the commit history.
