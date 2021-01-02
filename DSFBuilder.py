import struct
import hashlib
import os

class Atom:
    def __init__(self, title, packets):
        head = struct.pack('<4sI', title, 8 + sum(len(p) for p in packets))
        self.packets = [p for ps in [[head], packets] for p in ps]

    def get_packets(self):
        return self.packets

class AtomAtom(Atom):
    def __init__(self, title, atoms):
        packets = [p for atom in atoms for p in atom.get_packets()]
        super().__init__(title, packets)

class StringAtom(Atom):
    def __init__(self, title, strings):
        terminated = ([s, '\0'] for s in strings)
        packets = (s.encode('UTF-8') for t in terminated for s in t)
        super().__init__(title, packets)

def write_dsf(filename, atoms):
    head = b'XPLNEDSF\x01\0\0\0'
    content = bytes(b for item in [[head], (p for a in atoms for p in a.get_packets())] for packets in item for p in packets for b in p)
    footer = hashlib.md5(content).digest()
    tmpname = filename + '.tmp'
    with open(tmpname, 'wb') as f:
        f.write(content)
        f.write(footer)
    os.replace(tmpname, filename)
