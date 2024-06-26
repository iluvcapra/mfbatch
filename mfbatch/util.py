# util.py 

def readline_with_escaped_newlines(f):
    line = ''
    while True:
        line += f.readline()
        
        if len(line) == 0:
            break 

        line = line.rstrip("\n")

        if len(line) > 0 and line[-1] == '\\':
            line = line[:-1]
            continue

        else:
            yield line 
            line = ''

