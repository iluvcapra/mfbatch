"""
mfbatch commands - commands, batchfile parser and errors
"""

# from string import Template
import sys
import shlex
import shutil
import re
import os.path

from typing import Dict, Tuple, Optional

from mfbatch.metaflac import write_metadata as flac


class UnrecognizedCommandError(Exception):
    "A command in the batchfile was not recognized"
    command: str
    line: int

    def __init__(self, command, line) -> None:
        self.command = command
        self.line = line


class CommandArgumentError(Exception):
    """
    A command line in the batchfile did not have the correct number of argumets
    """

    command: str
    line: int

    def __init__(self, command, line) -> None:
        self.command = command
        self.line = line


class CommandEnv:
    """
    Stores values and state for commands
    """
    metadatums: Dict[str, str]
    incr: Dict[str, str]
    patterns: Dict[str, Tuple[str, str, str]]
    onces: Dict[str, Optional[str]]

    artwork_file: Optional[str]
    artwork_desc: Optional[str]

    def __init__(self) -> None:
        self.metadatums = {}
        self.incr = {}
        self.patterns = {}
        self.onces = {}

    def unset_key(self, k):
        """
        Delete a key from the environment
        """
        del self.metadatums[k]

        self.incr.pop(k, None)
        self.patterns.pop(k, None)

    def reset_keys(self):
        """
        Reset all keys in the environment
        """
        all_keys = list(self.metadatums.keys())

        for key in all_keys:
            self.unset_key(key)

        self.patterns = {}
        self.incr = {}

    def set_pattern(self, to: str, frm: str, pattern: str, repl: str):
        """
        Establish a pattern replacement in the environment
        """
        self.patterns[to] = (frm, pattern, repl)

    def evaluate_patterns(self):
        """
        Evaluate all patterns, this must run once and exactly once before 
        writing file metadata.
        """
        for to_key, (from_key, pattern, replacement) in self.patterns.items():
            from_value = self.metadatums[from_key]
            self.metadatums[to_key] = re.sub(pattern, replacement, from_value)

    def set_once(self, key, value):
        """
        Establish a set-once key 
        """
        self.onces[key] = self.metadatums.get(key, None)
        self.metadatums[key] = value

    def set_file_keys(self, path):
        """
        Establish the special file keys.
        """
        apath = os.path.abspath(path)
        self.metadatums['_ABSPATH'] = apath
        dirname, self.metadatums['_FILENAME'] = os.path.split(apath)
        _, self.metadatums['_FOLDER'] = os.path.split(dirname)

    def clear_file_keys(self):
        """
        Delete the special file keys.
        """
        del self.metadatums['_ABSPATH']
        del self.metadatums['_FILENAME']
        del self.metadatums['_FOLDER']

    def revert_onces(self):
        """
        Revert all set-once keys.
        """
        keys = list(self.onces)
        for key in keys:
            del self.metadatums[key]
            if self.onces[key] is not None:
                self.metadatums[key] = self.onces[key] or ''

            del self.onces[key]

    def increment_all(self):
        """
        Increment all increment keys.
        """
        for k, v in self.incr.items():
            v = int(v)
            self.metadatums[k] = self.incr[k] % (v + 1)


class BatchfileParser:
    """
A batchfile is a text file of lines. Lines either begin with a '#' to denote a
comment, a ':' to denote a Command, and if neither of these are present, the
line is interpreted as a file path to act upon. Empty lines are ignored.

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
        self.write_metadata_f = flac

    def eval(self, line: str, lineno: int, interactive: bool):
        """
        Accept a line from the file and act on it.
        """
        if line.startswith(self.COMMAND_LEADER):
            self._handle_command(line.lstrip(self.COMMAND_LEADER), lineno)
        elif line.startswith(self.COMMENT_LEADER):
            self._handle_comment(line.lstrip(self.COMMENT_LEADER))
        else:
            self._handle_file(line, interactive)

    def _handle_command(self, line, lineno):
        args = shlex.split(line)
        actions = [m_name for m_name in dir(self)
                   if not (m_name.startswith('_') or m_name == 'eval')]

        if args[0] in actions:
            try:
                getattr(self, args[0])(args[1:])
            except KeyError as exc:
                raise CommandArgumentError(command=args[0],
                                           line=lineno) from exc
        else:
            raise UnrecognizedCommandError(command=args[0], line=lineno)

    def _handle_comment(self, _):
        pass

    def _write_metadata_impl(self, line):
        if self.dry_run:
            print("DRY RUN would write metadata here.")
        else:
            sys.stdout.write("Writing metadata... ")
            self.write_metadata_f(line, self.env.metadatums)
            sys.stdout.write("Complete!")

        self.env.increment_all()
        self.env.revert_onces()
        self.env.clear_file_keys()

    def _print_kv_columnar(self, key, value):
        line_len = int(shutil.get_terminal_size()[0]) - 32
        value_lines = [value[i:i+line_len] for i in
                       range(0, len(value), line_len)]

        for l in value_lines:
            if key:
                sys.stdout.write(f"{key:.<30}  \033[4m{l}\033[0m\n")
                key = None
            else:
                sys.stdout.write(f"{' ' * 30}  \033[4m{l}\033[0m\n")

    def _handle_file(self, line, interactive):
        while True:

            self.env.set_file_keys(line)
            self.env.evaluate_patterns()

            if self.dry_run:
                sys.stdout.write(f"\nDRY RUN File: \033[1m{line}\033[0m\n")
            else:
                sys.stdout.write(f"\nFile: \033[1m{line}\033[0m\n")

            for key, value in self.env.metadatums.items():

                if key.startswith('_'):
                    continue

                self._print_kv_columnar(key, value)

            if interactive:
                val = input('Write? [Y/n/a/:] > ')
                if val == '' or val[0].upper() == 'Y':
                    self._write_metadata_impl(line)
                    break
                if val.startswith(self.COMMAND_LEADER):
                    self._handle_command(val.lstrip(self.COMMAND_LEADER),
                                         lineno=-1)
                elif val == 'a':
                    print("Aborting write session...", file=sys.stdout)
                    break
            else:
                self._write_metadata_impl(line)
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

    def set1(self, args):
        """
        set1 KEY VALUE 
        KEY is set to VALUE for the next file only. After the next file is 
        written the value of KEY reverts to its previous value
        """
        key = args[0]
        value = args[1]
        self.env.set_once(key, value)

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
        no keys set, including keys set by the `setinc` and `setp` commands.
        """
        all_keys = list(self.env.metadatums.keys())
        for k in all_keys:
            self.env.unset_key(k)

    def setinc(self, args):
        """
        setinc KEY INITIAL [FORMAT]
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

        self.env.metadatums[key] = fmt % (int(initial))
        self.env.incr[key] = fmt

    def setp(self, args):
        """
        setp KEY INPUT PATTERN REPL
        KEY will be set to the result of re.sub(PATTERN, REPL, INPUT). Patterns
        are evaluated in the order they appear in the batchfile, once for each 
        file that appears in the batchfile before writing. INPUT can be KEY or 
        use the special keys _FILENAME, _ABSPATH, and _FOLDER.
        """
        key = args[0]
        inp = args[1]
        pattern = args[2]
        repl = args[3]
        self.env.set_pattern(key, inp, pattern, repl)

    def d(self, args):
        """
        d VALUE
        An alias for "set1 DESCRIPTION VALUE".
        """
        val = args[0]
        self.env.set_once('DESCRIPTION', val)
