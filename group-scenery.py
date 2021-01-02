import shutil
import sys
import os
import scenery as s

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
