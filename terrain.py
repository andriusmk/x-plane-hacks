file_keywords = [
    'BASE_TEX',
    'LIT_TEX',
    'BORDER_TEX',
    'COMPOSITE_TEX',
    'COMPOSITE_BORDERS',
    'BASE_TEX_NOWRAP',
    'COMPOSITE_NOWRAP',
    'LIT_TEX_NOWRAP',
    'BORDER_TEX_WRAP'
]

def split_kwd_value(line):
    return tuple(line.strip().split(maxsplit = 1))

def get_files_used(ter_file):
    lines = []
    with open(ter_file) as f:
        lines = f.readlines()

    return [kv[1].strip() for kv in (split_kwd_value(l) for l in lines) if kv and kv[0] in file_keywords]
