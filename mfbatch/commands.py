# commands.py 
# mfbatch 

# from string import Template
import sys
import shlex
import shutil
import re

import mfbatch.metaflac as flac

from typing import Dict, Tuple


class UnrecognizedCommandError(Exception):
    command: str
    line: int 

    def __init__(self, command, line) -> None:
        self.command = command 
        self.line = line

class CommandArgumentError(Exception):
    command: str
    line: int 

    def __init__(self, command, line) -> None:
        self.command = command 
        self.line = line


class CommandEnv:
    metadatums: Dict[str, str]
    incr: Dict[str, str]
    patterns: Dict[str, Tuple[str, str, str]]

    def __init__(self) -> None:
        self.metadatums = dict()
        self.incr = dict()
        self.patterns = dict()

    def unset_key(self, k):
        del self.metadatums[k]

        self.incr.pop(k, None)
        self.patterns.pop(k, None)

    def set_pattern(self, to: str, frm: str, pattern: str, repl: str):
        self.patterns[to] = (frm, pattern, repl)

    def evaluate_patterns(self):
        for to_key in self.patterns.keys():
            from_key, pattern, replacement = self.patterns[to_key]
            from_value = self.metadatums[from_key]
            self.metadatums[to_key] = re.sub(pattern, replacement, from_value)

    def increment_all(self):
        for k in self.incr.keys():
            v = int(self.metadatums[k])
            self.metadatums[k] = self.incr[k] % (v + 1)
            
    
class BatchfileParser:
    """
A batchfile is a text file of lines. Lines either begin with a '#' to denote a
comment, a ':' to denote a Command, and if neither of these are present, the
are interpreted as a file path to act upon. Empty lines are ignored.

If a line ends with a backslash '\\', the backslash is deleted and the contents
of the following line are appended to the end of the present line.

Commands precede the files that they act upon, and manipulate the values of
"keys" in an internal dictionary. These keys are what are written to files as
they appear in the batchfile.
    """

    dry_run: bool
    env: CommandEnv
    
    COMMAND_LEADER = ':'
    COMMENT_LEADER = '#'


    def __init__(self):
        self.dry_run = True 
        self.env = CommandEnv()

    def _handle_line(self, line:str, lineno: int, interactive: bool = True):
        if line.startswith(self.COMMAND_LEADER):
            self._handle_command(line.lstrip(self.COMMAND_LEADER), lineno)
        elif line.startswith(self.COMMENT_LEADER):
            self._handle_comment(line.lstrip(self.COMMENT_LEADER))
        else:
            self._handle_file(line, interactive)

    def _handle_command(self, line, lineno):
        args = shlex.split(line)
        actions = [member for member in dir(self) \
                if not member.startswith('_')]

        if args[0] in actions:
            try:
                self.__getattribute__(args[0])(args[1:])
            except KeyError:
                raise CommandArgumentError(command=args[0], line=lineno)
        else:
            raise UnrecognizedCommandError(command=args[0], line=lineno)

    def _handle_comment(self, _):
        pass

    def _handle_file(self, line, interactive): 
        while True:
            self.env.evaluate_patterns()

            if self.dry_run:
                sys.stdout.write(f"\nDRY RUN File: \033[1m{line}\033[0m\n")
            else:
                sys.stdout.write(f"\nFile: \033[1m{line}\033[0m\n")            

            for key in self.env.metadatums.keys():

                if key.startswith('_'):
                    continue 

                value = self.env.metadatums[key]

                LINE_LEN = int(shutil.get_terminal_size()[0]) - 32
                value_lines = [value[i:i+LINE_LEN] for i in \
                        range(0,len(value), LINE_LEN)]
                
                for l in value_lines:
                    if key:
                        sys.stdout.write(f"{key:.<30}  \033[4m{l}\033[0m\n")
                        key = None
                    else:
                        sys.stdout.write(f"{' ' * 30}  \033[4m{l}\033[0m\n")
            
            if interactive:
                    val = input('Write? [Y/n/:] > ')
                    if val == '' or val.startswith('Y') or val.startswith('y'):
                        if self.dry_run:
                            print("DRY RUN would write metadata here.")
                        else:
                            flac.write_metadata(line, self.env.metadatums)

                        self.env.increment_all()

                    elif val.startswith(self.COMMAND_LEADER):
                        self._handle_command(val.lstrip(self.COMMAND_LEADER), 
                                             lineno=-1)
                        continue

                    break
            else:
                break


    def set(self, args):
        """
        set KEY VALUE
        KEY in each subsequent file appearing in the transcript will be set to
        VAL. If KEY begins with an underscore, it will be set in the internal
        environment but will not be written to the file. 
        """
        key = args[0]
        value = args[1]
        self.env.metadatums[key] = value 

    def unset(self, args):
        """
        unset KEY 
        KEY in each subsequent file will not be set, the existing value for KEY
        is deleted.
        """
        key = args[0]
        self.env.unset_key(key)

    def reset(self, _):
        """
        reset 
        All keys in the environment will be reset, subsequent files will have 
        no keys set.
        """
        all_keys = list(self.env.metadatums.keys())
        for k in all_keys:
            self.env.unset_key(k)

    def seti(self, args):
        """
        seti KEY INITIAL [FORMAT]
        KEY in the next file appearing in the batchfile will be set to INITIAL,
        which must be an integer. INITIAL will then be incremented by one and
        this process will be repeated for each subsequent file in the
        batchfile. If FORMAT is given, it will be used to format the the
        integer value when setting, FORMAT is a python printf-style string and
        the default is "%i".
        """
        key = args[0]
        initial = args[1]
        fmt = '%i'
        if len(args) > 2:
            fmt = args[2]

        self.env.metadatums[key] = initial
        self.env.incr[key] = fmt

    def setp(self, args):
        """
        setp KEY INPUT PATTERN REPL
        KEY will be set to the result of re.sub(PATTERN, REPL, INPUT). Patterns
        are evaluated in the order they appear in the batchfile, once for each 
        file that appears in the batchfile before writing.
        """
        key = args[0]
        inp = args[1]
        pattern = args[2]
        repl = args[3]
        self.env.set_pattern(key,inp,pattern, repl)
        
    
    

