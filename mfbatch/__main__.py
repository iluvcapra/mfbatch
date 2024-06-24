# __main__.py 

import sys
from subprocess import run
import os
from glob import iglob
from re import match
from optparse import OptionParser
import shlex

from tqdm import tqdm

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
#   set-pattern TO FROM PATTERN 
#       Set key TO to FROM after matching against PATTERN in each subsequent 
#       file.
#   rename ARGUMENTS
#       Subsequent files will be renamed using rename(1). ARGUMENTS will be
#       passed to the command with the old name at the end.



METAFLAC_PATH = '/opt/homebrew/bin/metaflac'
COMMAND_PROCHAR = ':'
COMMENT_PROCHAR = '#'

def process_command(metadatums: dict, line: str, dry_run: bool):
    commandline = line.lstrip(COMMAND_PROCHAR).rstrip("\n")
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


def process_file(metadatums: dict, line: str, dry_run: bool):
    line = line.rstrip("\n")
    if dry_run:
        sys.stderr.write(f"process_file: {line}\n")
        sys.stderr.write(f"process_file: {metadatums}\n")
    else:
        pass


def execute_batch_list(batch_list_path: str, dry_run: bool):
    with open(batch_list_path, mode='r') as f:
        metadatums = {}
        while True: 
            line = f.readline() 
            if line is None or line == "":
                break 
            
            if line.startswith(COMMENT_PROCHAR):
                continue 
            
            elif line.startswith(COMMAND_PROCHAR):
                process_command(metadatums, line, dry_run)

            elif line == "\n":
                continue
            
            else:
                process_file(metadatums, line, dry_run)



if __name__ == "__main__":
    
    editor = os.getenv('EDITOR')

    op = OptionParser(usage="%prog [options]")
    op.add_option('-d', metavar='DIR',
                  help='chdir to DIR before running',
                  default=None) 
    op.add_option('-e', metavar='EDITOR',
                  help="Set editor (default is $EDITOR)",
                  default=editor)
    op.add_option('-f', metavar='FILE',
                  help="Write batch list file to FILE",
                  default='MFBATCH_LIST')
    options, args = op.parse_args()

    if options.d is not None:
        os.chdir(options.d)

    command_file = options.f 

    with open(command_file, mode='w') as f:
        f.write("# mfbatch\n\n")
        metaflac_command = [METAFLAC_PATH, '--list']
        metadatums = {}
        preflight = len(list(iglob('./**/*.flac', recursive=True)))
        for path in tqdm(iglob('./**/*.flac', recursive=True), total=preflight):
            result = run(metaflac_command + [path], capture_output=True)
            this_file_metadata = {}
            for line in result.stdout.decode('utf-8').splitlines():
                m = match(r'^\s+comment\[\d\]: ([A-Z]+)=(.*)$', line)
                if m is not None:
                    this_file_metadata[m[1]] = m[2]

            for this_key in this_file_metadata.keys():
                if this_key not in metadatums:
                    f.write(f":set {this_key} {shlex.quote(this_file_metadata[this_key])}\n")
                    metadatums[this_key] = this_file_metadata[this_key]
                else:
                    if this_file_metadata[this_key] != metadatums[this_key]:
                        f.write(f":set {this_key} {shlex.quote(this_file_metadata[this_key])}\n")
                        metadatums[this_key] = this_file_metadata[this_key]

            keys = list(metadatums.keys())
            for key in keys:
                if key not in this_file_metadata.keys():
                    f.write(f":unset {key}\n")
                    del metadatums[key]

            f.write(path + "\n\n")
    
    # list_stat = os.stat(command_file)

    editor_command = [options.e, command_file]
    run(editor_command)

    execute_batch_list(command_file, dry_run=True)

    # new_stat = os.stat(command_file)


    

