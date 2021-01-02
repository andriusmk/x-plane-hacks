import shutil
import sys
import os
import scenery as s
import DSFParser as p
import DSFBuilder as b

class BaseConverter(p.DSFParser):
    def __init__(self, stream):
        super().__init__(stream)
        self.build_atoms = []

    def convert_atoms(self, atom, make_parser):
        result = atom.parse_atoms(make_parser)
        self.build_atoms.append(b.AtomAtom(atom.title, result.build_atoms))
        return result

    def pass_atom(self, atom):
        bs = atom.get_bytes()
        self.build_atoms.append(b.Atom(atom.title, [bs]))
        return bs

class RootConverter(BaseConverter):
    def __init__(self, stream):
        super().__init__(stream)
        self.head = None
        self.defn = None

    def got_atom(self, atom):
        if atom.title == b'DAEH':
            self.head = self.convert_atoms(atom, HeadConverter)
        if atom.title == b'NFED':
            self.defn = self.convert_atoms(atom, lambda s: DefnConverter(s, self.head))
        else:
            self.pass_atom(atom)

class HeadConverter(BaseConverter):
    def __init__(self, stream):
        super().__init__(stream)
        self.south = None
        self.west = None

    def got_atom(self, atom):
        self.pass_atom(atom)
        if atom.title == b'PORP':
            dic = atom.get_string_dict()
            self.south = int(dic['sim/south'])
            self.west = int(dic['sim/west'])

class DefnConverter(BaseConverter):
    def __init__(self, stream, head):
        super().__init__(stream)
        self.head = head
        self.prefix = os.path.join('data','{0:+02d}{1:+03d}', '{2:+02d}{3:+03d}') \
            .format((head.south // 10) * 10, (head.west // 10) * 10, head.south, head.west)
        self.extfiles = []

    def got_atom(self, atom):
        if atom.title == b'TRET':
            conv = lambda s: os.path.join(self.prefix, s) if s.endswith('.ter') else s
            tert = list(atom.get_strings())
            self.build_atoms.append(b.StringAtom(atom.title, [conv(s) for s in tert]))
            self.extfiles = [s for s in tert if s.endswith('.ter')]
        else:
            self.pass_atom(atom)        

def convert_dsf(src, dest):
    result = None
    with p.open_dsf(src) as dsf:
        result = RootConverter(dsf).parse_atoms()
    b.write_dsf(dest, result.build_atoms)
    return result

def exec_and_pass(arg, action):
    action()
    return arg

def link_scenery(indir, outdir):
    files = s.get_files_used(indir)
    dirs = set(os.path.dirname(f) for f in files)
    for d in dirs:
        os.makedirs(os.path.join(outdir, d), exist_ok = True)
#        print('Create dir:', os.path.join(outdir, d))
    for f in files:
#        shutil.move(os.path.join(indir, f), os.path.join(outdir, f))
        outfile = os.path.join(outdir, f)
        if os.path.isfile(outfile):
            print('Not linking', outfile, ', file exists')
        else:
            os.link(os.path.join(indir, f), outfile)
#        print('Move', os.path.join(indir, f), 'to', os.path.join(outdir, f))

if __name__ == "__main__":
    dirs = list(sys.argv[1:])
    outdir = dirs.pop()
    for d in dirs:
        link_scenery(d, outdir)
#    files = [exec_and_pass(f, lambda: os.path.isfile(f) or exit('Broken scenery, "' + f + '" not found.')) for f in (os.path.join(d, f) for d in dirs for f in s.get_files_used(d))]
#    filedirs = set(os.path.dirname(f) for f in files)
#    print(filedirs)
