import os
import sys
import argparse
from ctrans.ctransmanager import CTransManager

def main():

    parser = argparse.ArgumentParser(
        usage='%(prog)s [-o outdir] indir',
        description='Initialize ctrans files for document.',
    )
    parser.add_argument(
        'srcdir',
        help='Pathname for the original files.'
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

    if not os.path.exists(args.srcdir):
        parser.error("srcdir not exist: %s" % args.srcdir)

    if os.path.exists(args.outdir):
        if args.srcdir == args.outdir:
            parser.error("outdir should not be equal to srcdir: %s" % args.outdir)

    manager = CTransManager(args.extention, args.replacedir)
    manager.create_ctransfiles(args.srcdir, args.outdir)

if __name__ == "__main__":
    main()
