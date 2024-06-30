# __main__.py 

import os
from glob import glob
from subprocess import run

from optparse import OptionParser
import shlex


from mfbatch.util import readline_with_escaped_newlines
import mfbatch.metaflac as flac
from mfbatch.commands import BatchfileParser 


from tqdm import tqdm
# import readline

def execute_batch_list(batch_list_path: str, dry_run: bool):
    with open(batch_list_path, mode='r') as f:
        parser = BatchfileParser()
        parser.dry_run = dry_run

        for line, line_no in readline_with_escaped_newlines(f):
            if len(line) > 0:
                parser._handle_line(line, line_no)


def create_batch_list(command_file: str):

    with open(command_file, mode='w') as f:
        f.write("# mfbatch\n\n")
        metadatums = {}
        flac_files = glob('./**/*.flac', recursive=True)
        flac_files = sorted(flac_files)
        for path in tqdm(flac_files, unit='File', desc='Scanning FLAC files'):
            this_file_metadata = flac.read_metadata(path) 
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
        create_batch_list(options.batchfile)

    if options.edit:
        editor_command = [os.getenv('EDITOR'), options.batchfile]
        run(editor_command)

    if options.write:
        execute_batch_list(options.batchfile, dry_run=options.dry_run)


if __name__ == "__main__":
    main()
    

