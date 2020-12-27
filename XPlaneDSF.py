import struct
import tempfile
#import py7zr
import os

class InvalidFileError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class CompressedDSFError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Atom:
    def __init__(self, fname, from_bytes, subtree = None):
        self.fname = fname
        self.from_bytes = from_bytes
        self.subtree = subtree

class XPlaneDSF:
    """Derive from this class and implement methods gotXXXX()
where XXXX is the 4 letter atom name. Method arguments are atom-specific.
Call parse() to parse the file. This parser is ***INCOMPLETE***."""

    @staticmethod
    def passthrough(bs):
        return bs

    @staticmethod
    def to_strings(bs):
        return [s for s in bs.decode('UTF-8').split('\0') if s]

    @staticmethod
    def to_string_dic(bs):
        ss = XPlaneDSF.to_strings(bs)
        return dict((ss[i], ss[i + 1]) for i in range(0, len(ss), 2))

    @staticmethod
    def to_demi(bs):
        return struct.unpack('<BBHIIff', bs)

    # DSF file tree
    tree = {
        b'DAEH' : Atom('gotHEAD', None, {
            b'PORP' : Atom('gotPROP', to_string_dic)
        }),
        b'NFED' : Atom('gotDEFN', None, {
            b'TRET' : Atom('gotTERT', to_strings),
            b'TJBO' : Atom('gotOBJT', to_strings),
            b'YLOP' : Atom('gotPOLY', to_strings),
            b'WTEN' : Atom('gotNETW', to_strings)
        }),
        b'SMED' : Atom('gotDEMS', None, {
            b'IMED' : Atom('gotDEMI', to_demi),
            b'DMED' : Atom('gotDEMD', passthrough)
        })
    }

    def read_atoms(self, file, size, tree):
        """Internal method."""
        endpos = file.tell() + size
        while file.tell() < endpos:
            key, asize = struct.unpack('<4sI', file.read(8))
            content_read = False
            # Unknown (not interesting) atoms are just skipped
            if key in tree:
                atom = tree[key]
                attr = getattr(self, atom.fname, None)
                if atom.subtree:
                    if callable(attr):
                        attr()
                    # If the parser is interested in any of subatoms, parse the atom of atoms
                    if any([callable(getattr(self, a.fname, None)) for a in atom.subtree.values()]):
                        self.read_atoms(file, asize - 8, atom.subtree)
                        content_read = True
                else:
                    if callable(attr):
                        attr(atom.from_bytes.__get__(self)(file.read(asize - 8)))
                        content_read = True

            # If atom content was not read, skip it
            if not content_read:
                file.seek(asize - 8, 1)

    def parse(self, file, tmpdir = None):
        """Parse the DSF file. Un-7zip it if needed. A directory for decompressed
file may be specified, if not, it will be created."""
        try:
            with open(file, 'rb') as f:
                header = f.read(12)
                if len(header) < 12:
                    raise InvalidFileError()

                cookie, version = struct.unpack('<8sI', header)

                # Handle 7zip compressed files
                if cookie.startswith(b'7z'):
                    raise CompressedDSFError()

                # The file cookie and version must be valid
                if cookie != b'XPLNEDSF' or version != 1:
                    raise InvalidFileError()

                # Find data area size
                f.seek(0, 2)
                section_size = f.tell() - (16 + 12)
                f.seek(12, 0)

                # Parse data area
                self.read_atoms(f, section_size, XPlaneDSF.tree)

        # Handle 7zip compressed files here
        except CompressedDSFError:
            # Extract into a temporary directory.
            # If it's not provided by the user, create a new one and discard it after use.
            if not tmpdir:
                with tempfile.TemporaryDirectory() as tmp:
                    self.decompress_and_parse(file, tmp)
            else:
                self.decompress_and_parse(file, tmpdir)
        return self

    def decompress_and_parse(self, file, tmpdir):
        """Internal method."""
        os.system('7z e -o' + tmpdir + " '" + file + "'")
#        with py7zr.SevenZipFile(file, mode='r') as z:
#            z.extractall(tmpdir)
        self.parse(os.path.join(tmpdir, os.path.basename(file)))
        
