# mfbatch

I've been reorganzing my sound effects library recently and have had to edit a 
large number of FLAC files, adding and editing descriptions, normalizing 
fields etc. and this is one of the tools I've come up with for updating a large
number of FLAC files in an easy qay quickly. It works completely in the command
line and is designed to be used with your favorite text editor.

## Workflow

1) Create a new `MFBATCH_LIST` file for a directory of FLAC files.

```sh 
$ cd path/to/my/flacs 
$ mfbatch -c 
```

2) Edit the `MFBATCH_LIST` file in vim, or nano, or whatever your favorite text
editor is.

```sh 
$ mfbatch --edit
```

The `MFBATCH_LIST` file will contain a transcript of all of the flac files 
in the selected folder along with their current metadata.

```sh 

:set ALBUM 'Test Album 1'
:set DESCRIPTION 'Tone file #1, test tone 440Hz'
./tone1.flac

:set DESCRIPTION 'Tone file #2, also 440Hz'
./tone2.flac
:unset DESCRIPTION

./tone3.flac
```

3) After you've made the changes you want to make, write them to the files.

```sh 
$ mfbatch -W
```
