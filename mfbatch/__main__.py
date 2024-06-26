# __main__.py 

import sys
from subprocess import run
import os
from glob import glob
from re import match
from optparse import OptionParser
import shlex

from typing import List


from mfbatch.util import readline_with_escaped_newlines

from tqdm import tqdm
# import readline

# MFBATCH COMMAND FILE
# Every line is processed, the first character decides the kind of command 
# in the style of mtree.
# [a-z] Line is a command 
# : Line is a file 
# # is a comment

# Commands are: 
#   set KEY REST 
#       KEY in each subsequent file is set to REST. 
#   unset KEY 
#       KEY in each subsequent file will be unset.
#   unset-all 
#       No keys in each subsequent file will be set.
#   set-incr KEY INITIAL
#       KEY in next file will be set to INITIAL which will be incremented by 
#       one for each file processed.
#   set-pattern TO FROM PATTERN REPL 
#       Set key TO to FROM after matching against PATTERN in each subsequent 
#       file.
#   rename ARGUMENTS
#       Subsequent files will be renamed using rename(1). ARGUMENTS will be
#       passed to the command with the old name at the end.



METAFLAC_PATH = '/opt/homebrew/bin/metaflac'
COMMAND_LEADER = ':'
COMMENT_LEADER = '#'


class CommandEnv:
    metadatums: dict
    incr: List[str]

    def __init__(self) -> None:
        self.metadatums = dict()
        self.incr = []


def handle_command(metadatums: dict, line: str, dry_run: bool):
    commandline = line.lstrip(COMMAND_LEADER)
    args = shlex.split(commandline)
    command = args[0]

    if command == 'set':
        key = args[1]
        value = args[2]
        metadatums[key] = value
    
    elif command == 'unset':
        key = args[1]
        del metadatums[key]

    elif command == 'unset-all': 
        all_keys = list(metadatums.keys())
        for k in all_keys:
            del metadatums[k]
            
    elif command == 'set-incr':
        pass 

    elif command == 'set-pattern':
        pass
    
    elif command == 'rename':
        pass
    
    else:
        sys.stderr.write(f"Unrecognized command line: {line}\n")


def process_flac_file(metadatums: dict, line: str, dry_run: bool):
    line = line.rstrip("\n")
    sys.stdout.write(f"\nFile: \033[1m{line}\033[0m\n")
    for key in metadatums.keys():
        value = metadatums[key]
        value_lines = [value[i:i+60] for i in range(0,len(value),60)]
        for l in value_lines:
            if key:
                sys.stdout.write(f"  {key:.<32} : \033[4m{l}\033[0m\n")
                key = None
            else:
                sys.stdout.write(f"  {' ' * 32}   \033[4m{l}\033[0m\n")

    
    resp = input('Confirm? [Y/n]: ')
    if resp in ['','Y','y']:
        if not dry_run:
            sys.stdout.write('!! Writing not implemented\n')
        else:
            sys.stdout.write('Dry-run, would write file here.\n')



def execute_batch_list(batch_list_path: str, dry_run: bool):
    with open(batch_list_path, mode='r') as f:
        metadatums = {}
        for line in readline_with_escaped_newlines(f):

            if line == '':
                continue

            elif line.startswith(COMMENT_LEADER):
                continue 
            
            elif line.startswith(COMMAND_LEADER):
                handle_command(metadatums, line, dry_run)

            else:
                process_flac_file(metadatums, line, dry_run)


def create_cwd_batch_list(command_file: str):
    metadatums = {}
    with open(command_file, mode='w') as f:
        f.write("# mfbatch\n\n")
        metaflac_command = [METAFLAC_PATH, '--list']
        flac_files = glob('./**/*.flac', recursive=True)
        flac_files = sorted(flac_files)
        for path in tqdm(flac_files, unit='File', desc='Scanning FLAC files'):
            result = run(metaflac_command + [path], capture_output=True)
            this_file_metadata = {}
            for line in result.stdout.decode('utf-8').splitlines():
                m = match(r'^\s+comment\[\d\]: ([A-Za-z]+)=(.*)$', line)
                if m is not None:
                    this_file_metadata[m[1]] = m[2]

            for this_key in this_file_metadata.keys():
                if this_key not in metadatums:
                    f.write(f":set {this_key} "
                            f"{shlex.quote(this_file_metadata[this_key])}\n")
                    metadatums[this_key] = this_file_metadata[this_key]
                else:
                    if this_file_metadata[this_key] != metadatums[this_key]:
                        f.write(f":set {this_key} "
                                f"{shlex.quote(this_file_metadata[this_key])}"
                                "\n")
                        metadatums[this_key] = this_file_metadata[this_key]

            keys = list(metadatums.keys())
            for key in keys:
                if key not in this_file_metadata.keys():
                    f.write(f":unset {key}\n")
                    del metadatums[key]

            f.write(path + "\n\n")


def main():
    op = OptionParser(usage="%prog [-c] [-W] [options]")
    
    op.add_option('-c', '--create', default=False,       
                  action='store_true',
                  help='Create a new list')
    op.add_option('-W', '--write', default=False, 
                  action='store_true',
                  help="Execute batch list, write to files")
    op.add_option('-p', '--path', metavar='DIR',
                  help='chdir to DIR before running',
                  default=None) 
    op.add_option('-e', '--edit', action='store_true',
                  help="Open batch file in the default editor",
                  default=False)
    op.add_option('-n', '--dry-run', action='store_true',
                  help="Dry-run -W.")
    op.add_option('-f', '--batchfile', metavar='FILE',
                  help="Use batch list FILE for reading and writing instead "
                  "of the default \"MFBATCH_LIST\"",
                  default='MFBATCH_LIST')

    options, _ = op.parse_args()

    if options.path is not None:
        os.chdir(options.path)

    if options.create:
        create_cwd_batch_list(options.batchfile)

    if options.edit:
        editor_command = [os.getenv('EDITOR'), options.batchfile]
        run(editor_command)

    if options.write:
        execute_batch_list(options.batchfile, dry_run=options.dry_run)


if __name__ == "__main__":
    main()
    

