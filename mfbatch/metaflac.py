# metaflac.py 
# mfbatch

from subprocess import run
from re import match
from io import StringIO

from typing import Dict 

METAFLAC_PATH = '/opt/homebrew/bin/metaflac'

FlacMetadata = Dict[str, str]


def sanatize_key(k: str) -> str:
    """
    Enforces the VORBIS_COMMENT spec with regard to keys
    """
    k = k.upper()
    rval = ''
    for c in k:
        v = ord(c)
        if 0x20 <= v <= 0x7D and v != 0x3D:
            rval = rval + c
        else:
            rval = rval + '_'

    return rval


def sanatize_value(v: str) -> str: 
    """
    Enforces the VORBIS_COMMENT spec with regard to values. Also removes 
    newlines, which are not supported by this tool.
    """

    return v.translate(str.maketrans('\n',' '))


def read_metadata(path: str, metaflac_path=METAFLAC_PATH) -> FlacMetadata:
    metaflac_command = [metaflac_path, '--list']
    result = run(metaflac_command + [path], capture_output=True)
    result.check_returncode()

    file_metadata = {}
    for line in result.stdout.decode('utf-8').splitlines():
        m = match(r'^\s+comment\[\d\]: ([A-Za-z]+)=(.*)$', line)
        if m is not None:
            file_metadata[m[1]] = m[2]

    return file_metadata


def write_metadata(path: str, data: FlacMetadata, 
                   metaflac_path=METAFLAC_PATH):
    remove_job = run([metaflac_path, '--remove-all-tags', path])
    remove_job.check_returncode()

    metadatum_f = "" 

    for k in data.keys():
        key = sanatize_key(k)
        val = sanatize_value(data[k])
        if key.startswith('_'):
            continue

        metadatum_f  = metadatum_f + f"{key}={val}\n"

    insert_job = run([metaflac_path, "--import-tags-from=-", path], 
                     input=metadatum_f.encode('utf-8'))
    insert_job.check_returncode()

