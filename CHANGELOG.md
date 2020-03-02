# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)

## [Unreleased]
### TODO
- support for latex input with images

## [0.4.4] - 2020-03-02
### Fixed
- Capture FileNotFoundError when `.esapyrc` doesn't exist.

## [0.4.3] - 2020-02-27
### Added
- `[--edit-in-browser | --no-browser]` option for `esa up`
  - open edit page on browser after publish
  - default: `--edit-in-browser`

## [0.4.2] - 2020-02-27
### Fixed
- image upload even when alt-text is ""

## [0.4.1] - 2020-02-27
### Fixed
- support latex input

## [0.4.0] - 2020-02-27
### Added
- proxy setting
- subcommand
  - `esa stats`
  - `esa publish`

### Changed
- automatically publish when `esa up ***.ipynb`



## [0.3.0] - 2020-02-27
### Added
- CHANGELOG.md
- subcommands
  - `esa up`
  - `esa convert`
  - `esa replace`
  - `esa config`
- help command

### Changed
- README.md
  - pypi badges
- command line call
- process logic
  - separete process
  - enable retry


### Removed
- some command removed.
  - `esa-up`
  - `esa-token`
  - `jupyter esa-up`



## [0.2.0] - 2020-02-24
### Added
- Markdown body is copid to clipboard after process.



## [0.1.2] - 2020-02-23
### Added
- first working release !
