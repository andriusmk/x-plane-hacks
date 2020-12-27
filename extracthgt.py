import sys
import getopt
import os
import struct
import XPlaneDSF as dsf

class HGTParser(dsf.XPlaneDSF):
    def __init__(self):
        self.current_demi = None
        self.demi_used = None
        self.hgt = None

    def gotDEMS(self):
        self.current_demi = None

    def gotDEMI(self, demi):
        self.current_demi = demi

    def gotDEMD(self, bs):
        if self.current_demi:
            ver, bpp, flags, w, h, scl, off = self.current_demi
            if ver != 1: return
            if bpp != 2: return
            if (flags & 3) != 1: return
            if w != 1201 or h != 1201: return
            if len(bs) != 2884802: return
            self.demi_used = self.current_demi
            self.hgt = list(struct.unpack('<1442401h', bs))

def extract_hgt(dsf, tmpdir = None):

    heights = HGTParser().parse(dsf, tmpdir).hgt
    heights_r = (heights[(1200 - (i // 1201)) * 1201 + (i % 1201)] for i in range(0, len(heights)))

    return struct.pack('>1442401h', *heights_r)

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

    with open(output, 'wb') as outfile:
        outfile.write(extract_hgt(args[0]))
