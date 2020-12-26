import sys
import getopt
import tempfile
import os
import struct

class DSF:
    pass

def read_atom(dsf):
    if (dsf.file.tell() >= dsf.size):
        return (bytes(), 0)
    buf = dsf.file.read(8)
    atom, size = struct.unpack('<4sI', buf)
    return (atom, size - 8)

def extract_hgt(dsf):
    while True:
        atom, size = read_atom(dsf)
        if size == 0:
            return bytes()
        if (atom == b'SMED'):
            subdsf = DSF()
            subdsf.file = dsf.file
            subdsf.size = dsf.file.tell() + size
            result = bytes()
            hgt3found = False
            while True:
                atom, size = read_atom(subdsf)
                if size == 0:
                    return result
                if atom == b'IMED':
                    ver, bpp, _, w, h = struct.unpack('<BBHII', subdsf.file.read(size)[:12])
                    if ver == 1 and bpp == 2 and w == 1201 and h == 1201:
                        hgt3found = True
                elif hgt3found and atom == b'DMED' and size == 2884802:
                    result = subdsf.file.read(size)
                else:
                    subdsf.file.seek(size, 1)
        else:
            dsf.file.seek(size, 1)

    return bytes()

def process_dsf(name, output):
    with open(name, 'rb') as file:
        head = file.read(8)
        if head == b'XPLNEDSF':
            buf = file.read(4)
            [version] = struct.unpack('<I', buf)
            if version != 1:
                sys.exit("Bad DSF version: " + str(version))
                return bytes()
            dsf = DSF()
            dsf.file = file
            file.seek(0, 2)
            dsf.size = file.tell() - 16
            file.seek(12, 0)
            res = extract_hgt(dsf)
            if res:
                vals = struct.unpack('<1442401h', res)
#                print(vals)
                vals_r = [vals[(1200 - (i // 1201)) * 1201 + (i % 1201)] for i in range(0, len(vals))]
                res_out = struct.pack('>1442401h', *vals_r)
                with open(output, 'wb') as outf:
                    outf.write(res_out)
            return None
        return head

def process_file(name, output):
    head = process_dsf(name, output)

    if head == None:
        print('Success!')
    elif head.startswith(b'7z'):
        fn = os.path.basename(name)
        with tempfile.TemporaryDirectory() as tmpdir:
            os.system('7z e -o' + tmpdir + " '" + name + "'")
            process_file(os.path.join(tmpdir, fn), output)
    else:
        print('Unknown file format')

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "o:", [])
    if len(args) < 1:
        sys.exit("""Syntax:
    extracthgt.py [-o <output>] file.dsf
    """)
    output = os.path.basename(args[0] + '.hgt')
    for opt, optarg in opts:
        if opt == "-o":
            output = optarg
    process_file(args[0], output)
