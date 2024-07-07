"""
mfbatch main - Command entrypoint for mfbatch
"""

import os
from glob import glob
from subprocess import run
import sys
from argparse import ArgumentParser
import shlex
from typing import Callable
import inspect

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


def create_batch_list(command_file: str, recursive=True):
    """
    Read all FLAC files in the cwd and create a batchfile that re-creates all
    of their metadata.
    """
    with open(command_file, mode='w', encoding='utf-8') as f:
        f.write("# mfbatch\n\n")
        metadatums = {}
        flac_files = glob('./**/*.flac', recursive=recursive)
        flac_files = sorted(flac_files)
        for path in tqdm(flac_files, unit='File', desc='Scanning FLAC files'):
            this_file_metadata = metadata_funcs.read_metadata(path)
            for this_key, this_value in this_file_metadata.items():
                if this_key not in metadatums:
                    f.write(f":set {this_key} "
                            f"{shlex.quote(this_value)}\n")
                    metadatums[this_key] = this_value
                else:
                    if this_value != metadatums[this_key]:
                        f.write(f":set {this_key} "
                                f"{shlex.quote(this_value)}"
                                "\n")
                        metadatums[this_key] = this_value

            keys = list(metadatums.keys())
            for key in keys:
                if key not in this_file_metadata:
                    f.write(f":unset {key}\n")
                    del metadatums[key]

            f.write(path + "\n\n")


def main():
    """
    Entry point implementation
    """
    op = ArgumentParser(
        prog='mfbatch', usage='%(prog)s (-c | -e | -W) [options]')

    op.add_argument('-c', '--create', default=False,
                    action='store_true',
                    help='create a new list')
    op.add_argument('-e', '--edit', action='store_true',
                    help="open batch file in the default editor",
                    default=False)
    op.add_argument('-W', '--write', default=False,
                    action='store_true',
                    help="execute batch list, write to files")

    op.add_argument('-p', '--path', metavar='DIR',
                    help='chdir to DIR before running',
                    default=None)
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
                    not command.startswith('_')]
        print(f"{inspect.cleandoc(BatchfileParser.__doc__ or '')}\n\n")
        for command in commands:
            meth = getattr(BatchfileParser, command)
            if isinstance(meth, Callable):
                print(f"{inspect.cleandoc(meth.__doc__ or '')}\n")

        sys.exit(0)

    mode_given = False
    if options.path is not None:
        os.chdir(options.path)

    if options.create:
        mode_given = True
        create_batch_list(options.batchfile)

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
