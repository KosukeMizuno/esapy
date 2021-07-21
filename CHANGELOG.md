# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)

## [Unreleased]
### TODO
- support for latex input with images
- check publish status and error-handling

## 2.0.0 - [2021-07-22]
### Added
- New feature: uploading to GROWI wiki system.

## 1.3.6 - [2021-03-15]
### Added
- Insert warnings for local editing.

### Fixed
- Handle an error when no args is provided.

## 1.3.5 - [2020-09-02]
### Added
- `esa ls` can recursively scan files in subfolder with `--recursive` option.

## 1.3.4 - [2020-08-19]
### Added
- `esa ls` can receive multiple-arguments as dirpath or filepath.
- Some options were added to `esa ls`.

## 1.3.3 - [2020-08-16]
### Fixed
- Unquoting URL encode of image tag in markdown cell of jupyter notebook. 

## 1.3.2 - [2020-06-13]
### Fixed
- Suppress meaningless error message during uploading a md file

## 1.3.1 - [2020-05-12]
### Fixed
- Calling `esa reset`  to set post_number in an ipynb file which has not been uploaded didn't work.

## 1.3.0 - [2020-05-10]
### Addded
- line/cell magic `esapy_fold` for code folding

### Removed
- check if a cell is a matplotlib cell by the first line -> magic command

## 1.2.0 - [2020-05-10]
### Fixed
- gathering post info by esa.io api before patch the post
- ignore message used in previous patch

### Changed
- sustain hashdict by esa-reset (default)

### Added
- record esapy version in metadata
  - if this module is git repo, record revision also.
- `esa reset`
  - `--clear-hashdict` option
  - `--number` option

## [1.1.1] - 2020-05-08
### Fixed
- Scrolling has been enabled.
- Single line output (proper close tag).

## [1.1.0] - 2020-05-05
### Added
- subcommand: `ls`
- subcommand: `reset`

## [1.0.3] - 2020-05-05
### Fixed
- WinError at removing temporary files
- post-mode option bug is fixed.

## [1.0.0] - 2020-05-05
### Added
- Enable folding in output markdown
  - ignore: any cell will be opened.
  - as-shown: cell folding obeys cell-metadata.
  - auto: a code cell starting with `plt.figure` will be folded.
- Hashlist of images
  - Once a image has been uploaded, it will never upload again. Upload history is recorded in metadata.
- Attachments
  - attached images can be extracted and uploaded.
- Math codeblock
  - simple latex equation environment `$$ ... $$` will be replaced as math-code block for avoiding mathjax escape.
- Work in temporary directory
  - No temporary files leave after process.

### Changed
- Internal process has been almost rewritten.

### Removed
- subcommands

## [0.5.0] - 2020-03-04
### Added
- Add output options
- Non-destrutive replace & upload can be used (Default: non-destructive).

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
