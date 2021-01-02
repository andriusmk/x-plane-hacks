import struct
import hashlib
import os

class Atom:
    def __init__(self, title, packets):
#        print(title, len(packets))
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
        packets = [s.encode('UTF-8') for t in terminated for s in t]
        super().__init__(title, packets)

def write_dsf(filename, atoms):
    head = b'XPLNEDSF\x01\0\0\0'
    atom_packets = (p for a in atoms for p in a.get_packets())
    packets = (p for ps in [[head], atom_packets] for p in ps)
    content = bytes(b for packet in packets for b in packet)
#   content = bytes(b for item in [[head], (p for a in atoms for p in a.get_packets())] for packets in item for p in packets for b in p)
    footer = hashlib.md5(content).digest()
    with open(filename, 'wb') as f:
        f.write(content)
        f.write(footer)
