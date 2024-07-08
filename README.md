![GitHub last commit](https://img.shields.io/github/last-commit/iluvcapra/mfbatch)
![](https://img.shields.io/github/license/iluvcapra/mfbatch.svg) ![](https://img.shields.io/pypi/pyversions/mfbatch.svg) [![](https://img.shields.io/pypi/v/mfbatch.svg)](https://pypi.org/project/mfbatch/) ![](https://img.shields.io/pypi/wheel/mfbatch.svg)

[![Lint and Test](https://github.com/iluvcapra/mfbatch/actions/workflows/pylint.yml/badge.svg)](https://github.com/iluvcapra/mfbatch/actions/workflows/pylint.yml)

# mfbatch

`mfbatch` is a command-line tool for batch-editing FLAC audio file metadata. 
It reads a directory of FLAC files, extracts the existing metadata to an 
intelligent text file format that the user can modify to update a large number
of files and dynamic per-file metadata with a minimal number of edits.

`mfbatch` is a front-end for `metaflac(1)` which must be installed on the
system.

## Motivation

I've been reorganzing my sound effects library recently and have had to edit a 
large number of FLAC files, adding and editing descriptions, normalizing 
fields etc. and this is one of the tools I've come up with for updating a large
number of FLAC files in an easy way quickly. It works completely in the command
line and is designed to be used with your favorite text editor.

## Workflow

### 1) Create a new `MFBATCH_LIST` file for a directory of FLAC files.

```sh 
$ cd path/to/my/flacs 
$ mfbatch -c 
```

`mfbatch` will scan the current working directory and 
all subdirectories recursively. You can use a `-p` option 
to switch to another directory before scanning.

### 2) Edit the `MFBATCH_LIST` file in your `$EDITOR`.
```sh 
$ mfbatch --edit
```

The `MFBATCH_LIST` file will contain a transcript of all of the flac files 
in the selected folder along with their current metadata.

```sh 
:set ALBUM 'Test Album 1'
:set ARTIST 'Test Artist'
:set DESCRIPTION 'Tone file #1, test tone 440Hz'
:setp TITLE DESCRIPTION "^Tone file #(\d+).*" 'Tone \1'
./tone1.flac

:set DESCRIPTION 'Tone file #2, also 440Hz'
./tone2.flac
:unset DESCRIPTION

:set DESCRIPTION 'Tone file #3'
./tone3.flac

```

The `MFBATCH_LIST` format allows you to set metadata once and then write values
to a run of files all at once. Several commands are available to manipulate
the metadata written to the files.

### 3) After you've made the changes you want to make, write them to the files.

```sh 
$ mfbatch -W
```

Writing metadata is interactive, `mfbatch` will display the
metdata to be written to each file and metadata can be
edited interactively at a prompt before writing.

## Limitations

* Does not support newlines in field values. This is mostly by choice, newlines
  don't offer any benefit in my preferred sound library programs but this
  wouldn't be a tough feature to add if anyone needed it.
* Does not support multiple artwork types, everything is stored as type `3`/
  (album artwork-front).
* Can only store unique field keys, field values of the same key overwrite old
  values. This is also something that is tailored to my use-case and could be
  changed if there was interest in doing so.
