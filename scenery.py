import os
import XPlaneDSF as dsf
import terrain as t

class DSFExtFilesParser(dsf.XPlaneDSF):
    def __init__(self):
        self.terrain_files = []

    def gotTERT(self, fs):
        self.terrain_files += fs

def list_dsfs(base_dir):
    dsf_base = os.path.join(base_dir, 'Earth nav data')

    # find all dirs with .dsf files
    interm_dirs = [subdir for subdir in os.listdir(dsf_base) if os.path.isdir(os.path.join(dsf_base, subdir))]

    # list .dsf files (relative paths)
    return [os.path.join('Earth nav data', subdir, dsf) for subdir in interm_dirs for dsf in os.listdir(os.path.join(dsf_base, subdir)) if dsf.endswith('.dsf')]

def get_files_used(base_dir):
    dsfs = list_dsfs(base_dir)
    ext_files = [f for dsf in dsfs for f in get_dsf_ext_files(base_dir, dsf)]

    # list all unique files (relative paths, unsorted)
    return set(dsfs + ext_files)

def get_dsf_ext_files(base_dir, dsf):
    terrain_files = [tf for tf in DSFExtFilesParser().parse(os.path.join(base_dir, dsf)).terrain_files if os.path.isfile(os.path.join(base_dir, tf))]

    # list all images referenced in .ter files (relative paths)
    images = [os.path.join(os.path.dirname(tf), im) for tf in terrain_files for im in t.get_files_used(os.path.join(base_dir, tf))]

    # list all unique files (relative paths, unsorted)
    return set(terrain_files + images)
