import os
import sys
import argparse
from ctrans.ctransmanager import CTransManager

def main():

    parser = argparse.ArgumentParser(
        usage='%(prog)s [-o outdir] srcdir transdir',
        description='Create ctrans files for document.',
    )
    parser.add_argument(
        'srcdir',
        help='Pathname for the original files.'
    )
    parser.add_argument(
        'transdir',
        help='Pathname for the ctrans files.'
    )
    parser.add_argument(
        '-o', '--outdir', default='.',
        help='Pathname for the ctrans files.'
    )
    parser.add_argument(
        '-E', '--extention', nargs='*', default=[],
        help='Target extentions for ctrans files.'
    )
    parser.add_argument(
        '-r', '--replacedir', nargs='*', default=[],
        help='Replace directory of ctrans files.'
    )

    args = parser.parse_args()

    manager = CTransManager(args.extention, args.replacedir)
    return manager.create_ctranslation_files(args.srcdir, args.transdir, args.outdir)

if __name__ == "__main__":
    main()
