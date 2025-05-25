"""
mfbatch main - Command entrypoint for mfbatch
"""

import os
from glob import glob
from subprocess import CalledProcessError, run
import sys
from argparse import ArgumentParser
import shlex
from typing import Callable, List, Tuple
import inspect
from io import StringIO

from tqdm import tqdm

from mfbatch.util import readline_with_escaped_newlines
import mfbatch.metaflac as metadata_funcs
from mfbatch.commands import BatchfileParser


def execute_batch_list(batch_list_path: str, dry_run: bool, interactive: bool):
    "Acts on a batch list"
    with open(batch_list_path, mode='r', encoding='utf-8') as f:
        parser = BatchfileParser()
        parser.dry_run = dry_run

        for line, line_no in readline_with_escaped_newlines(f):
            if len(line) > 0:
                parser.eval(line, line_no, interactive)


def sort_flac_files(file_list, mode):
    "Sort flac files"
    if mode == 'path':
        return sorted(file_list)
    if mode == 'mtime':
        return sorted(file_list, key=os.path.getmtime)
    if mode == 'ctime':
        return sorted(file_list, key=os.path.getctime)
    if mode == 'name':
        return sorted(file_list, key=os.path.basename)

    return file_list


def write_batchfile_entries_for_file(path, metadatums) -> Tuple[dict, str]:
    "Create batchfile entries for `path`"
    buffer = StringIO()

    try:
        this_file_metadata = metadata_funcs.read_metadata(path)

    except CalledProcessError as e:
        buffer.write(f"# !!! METAFLAC ERROR ({e.returncode}) while reading "
                     f"metadata from the file {path}\n\n")
        return metadatums, buffer.getvalue()

    for this_key, this_value in this_file_metadata.items():
        if this_key not in metadatums:
            buffer.write(f":set {this_key} "
                         f"{shlex.quote(this_value)}\n")
            metadatums[this_key] = this_value
        else:
            if this_value != metadatums[this_key]:
                buffer.write(f":set {this_key} "
                             f"{shlex.quote(this_value)}"
                             "\n")
                metadatums[this_key] = this_value

    keys = list(metadatums.keys())
    for key in keys:
        if key not in this_file_metadata:
            buffer.write(f":unset {key}\n")
            del metadatums[key]

    buffer.write(path + "\n\n")
    
    return metadatums, buffer.getvalue()


def create_batch_list(flac_files: List[str], command_file: str,
                      sort_mode='path'):
    """
    Read all FLAC files in the cwd and create a batchfile that re-creates all
    of their metadata.

    :param flac_files: Paths of files to create batchfile from 
    :param command_file: Name of new batchfile
    :param sort_mode: Order of paths in the batch list. Either 'path', 
        'mtime', 'ctime', 'name'
    :param input_files: FLAC files to scan
    """

    flac_files = sort_flac_files(flac_files, sort_mode)

    with open(command_file, mode='w', encoding='utf-8') as f:
        metadatums = {}

        f.write("# mfbatch\n\n")

        for path in tqdm(flac_files, unit='File',
                         desc='Scanning with metaflac...'):

            metadatums, buffer = write_batchfile_entries_for_file(path,
                                                                  metadatums)
            f.write(buffer)

        f.write("# mfbatch: create batchlist operation complete\n")


def main():
    """
    Entry point implementation
    """
    op = ArgumentParser(
        prog='mfbatch', usage='%(prog)s (-c | -e | -W) [options]')

    op.add_argument('-c', '--create', default=False,
                    action='store_true',
                    help='create a new list')
    op.add_argument('-F', '--from-file', metavar='FILE_LIST', action='store',
                    default=None, help="get file paths from FILE_LIST when "
                    "creating, instead of scanning directory"
                    "a new list")
    op.add_argument('-e', '--edit', action='store_true',
                    help="open batch file in the default editor",
                    default=False)
    op.add_argument('-W', '--write', default=False,
                    action='store_true',
                    help="execute batch list, write to files")
    op.add_argument('-p', '--path', metavar='DIR',
                    help='chdir to DIR before running',
                    default=None)
    op.add_argument('-s', '--sort', metavar='MODE', action='store',
                    default='path', help="when creating, Set mode to sort "
                    "files by. Default is 'path'. 'ctime, 'mtime' and 'name' "
                    "are also options.")
    op.add_argument('-n', '--dry-run', action='store_true',
                    help="dry-run -W.")
    op.add_argument('-f', '--batchfile', metavar='FILE',
                    help="use batch list FILE for reading and writing instead "
                    "of the default \"MFBATCH_LIST\"",
                    default='MFBATCH_LIST')
    op.add_argument('-y', '--yes', default=False, action='store_true',
                    dest='yes', help="automatically confirm all prompts, "
                    "inhibits interactive editing in -W mode")
    op.add_argument('--help-commands', action='store_true', default=False,
                    dest='help_commands',
                    help='print a list of available commands for batch lists '
                    'and interactive writing.')

    options = op.parse_args()

    if options.help_commands:
        print("Command Help\n------------")
        commands = [command for command in dir(BatchfileParser) if
                    not command.startswith('_') and command != "eval"]
        print(f"{inspect.cleandoc(BatchfileParser.__doc__ or '')}\n\n")
        for command in commands:
            meth = getattr(BatchfileParser, command)
            if isinstance(meth, Callable):
                print(f"- {inspect.cleandoc(meth.__doc__ or '')}\n")

        sys.exit(0)

    mode_given = False
    if options.path is not None:
        os.chdir(options.path)

    if options.create:
        mode_given = True
        flac_files: List[str] = []

        if options.from_file:
            with open(options.from_file, mode='r',
                      encoding='utf-8') as from_file:
                flac_files = [line.strip() for line in from_file.readlines()]
        else:
            flac_files = glob('./**/*.flac', recursive=True)

        # print(flac_files)
        create_batch_list(flac_files, options.batchfile,
                          sort_mode=options.sort)

    if options.edit:
        mode_given = True
        editor_command = [os.getenv('EDITOR'), options.batchfile]
        run(editor_command, check=True)

    if options.write:
        mode_given = True
        execute_batch_list(options.batchfile,
                           dry_run=options.dry_run,
                           interactive=not options.yes)

    if not mode_given:
        op.print_usage()
        sys.exit(-1)


if __name__ == "__main__":
    main()
