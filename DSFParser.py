import struct
from contextlib import contextmanager

class Stream:
    def __init__(self, file, length):
        self.file = file
        self.end_pos = file.tell() + length

    def is_finished(self):
        return self.file.tell() >= self.end_pos

def parse_atom(stream):
#    print('parse_atom', stream.file.tell(), stream.end_pos)
    if (stream.is_finished()): return None
    title, length = struct.unpack('<4sI', stream.file.read(8))
#    print('found', title, length)
    return Atom(title, stream, length - 8)

class InvalidFileError(Exception):
    pass

@contextmanager
def open_dsf(name):
    file = open(name, 'rb')
    try:
        cookie, version = struct.unpack('<8sI', file.read(12))
        if cookie != b'XPLNEDSF' or version != 1:
            raise InvalidFileError
        file.seek(0, 2)
        endpos = file.tell()
        file.seek(12, 0)
        yield Stream(file, endpos - (12 + 16))
    finally:
        file.close()

class Atom:
    def __init__(self, title, stream, length):
        self.stream = stream
        self.content = None
        self.title = title
        self.length = length
        self.content_read = False

    def get_bytes(self):
        if self.content:
            return self.content
        else:
            self.content = self.stream.file.read(self.length)
            self.content_read = True
            return self.content

    def finish(self):
        if not self.content_read:
            self.stream.file.seek(self.length, 1)
            self.content_read = True

    def parse_atoms(self, make_parser):
        substream = Stream(self.stream.file, self.length)
        parser = make_parser(substream)
        parser.parse_atoms()
        self.content_read = True
        return parser

    def get_strings(self):
        bs = self.get_bytes()
        return (s for s in bs.decode('UTF-8').split('\0') if s)

    def get_string_dict(self):
        ss = list(self.get_strings())
        return dict((ss[i], ss[i + 1]) for i in range(0, len(ss), 2))

class DSFParser:
    def __init__(self, stream):
        self.stream = stream

    def parse_atoms(self):
        while not self.stream.is_finished():
            atom = parse_atom(self.stream)
            self.got_atom(atom)
            atom.finish()
        return self

    def got_atom(self, atom):
        pass
