import shutil
import sys
import os
import scenery as s
import terrain as t
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
        elif atom.title == b'NFED':
            self.defn = self.convert_atoms(atom, lambda s: DefnConverter(s, self.head))
        else:
            self.pass_atom(atom)

    def get_extfiles(self):
        return self.defn.extfiles

    def get_data_prefix(self):
        return self.defn.prefix

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
        self.prefix = os.path.join('data','{0:+03d}{1:+04d}', '{2:+03d}{3:+04d}') \
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

def link_sceneries(indirs, outdir):
    datafiles = dict()
#    dsfs = (os.path.join(indir, dsf) for indir in indirs for dsf in s.list_dsfs(indir))
    for indir in indirs:
        dsfs = s.list_dsfs(indir)
        dsfdirs = set(os.path.dirname(d) for d in dsfs)
        for d in dsfdirs:
            os.makedirs(os.path.join(outdir, d), exist_ok = True)

        for dsf in dsfs:
            outname = os.path.join(outdir, dsf)
            tmpname = outname + '.tmp'
            print('Converting', os.path.join(indir, dsf))
            conv_result = convert_dsf(os.path.join(indir, dsf), tmpname)
            prefix = conv_result.get_data_prefix()
            terfiles = conv_result.get_extfiles()
            textures = set(os.path.join('terrain', ts) for ter in terfiles for ts in t.get_files_used(os.path.join(indir, ter)))
            extfiles = terfiles + list(textures)
            print(len(extfiles), 'external files')
            for d in set(os.path.dirname(ext) for ext in extfiles):
                os.makedirs(os.path.join(outdir, prefix, d), exist_ok = True)

            reused = 0
            for ext in extfiles:
                src_ext = None
                key = os.path.basename(ext)
                try:
                    src_ext = datafiles[key]
                    reused += 1
                except KeyError:
                    src_ext = os.path.join(indir, ext)
                    datafiles[key] = src_ext
#                print('linking', src_ext, '->', os.path.join(outdir, prefix, ext))    
                os.link(src_ext, os.path.join(outdir, prefix, ext))    

            os.replace(tmpname, outname)
            print('ok,', reused, 'files reused')

if __name__ == "__main__":
    dirs = list(sys.argv[1:])
    outdir = dirs.pop()
    link_sceneries(dirs, outdir)
#    files = [exec_and_pass(f, lambda: os.path.isfile(f) or exit('Broken scenery, "' + f + '" not found.')) for f in (os.path.join(d, f) for d in dirs for f in s.get_files_used(d))]
#    filedirs = set(os.path.dirname(f) for f in files)
#    print(filedirs)
