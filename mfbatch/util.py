# util.py

def readline_with_escaped_newlines(f):
    line = ''
    line_no = 0
    while True:
        line += f.readline()
        line_no += 1

        if len(line) == 0:
            break

        line = line.rstrip("\n")

        if len(line) > 0 and line[-1] == '\\':
            line = line[:-1]
            continue

        else:
            yield line, line_no
            line = ''
