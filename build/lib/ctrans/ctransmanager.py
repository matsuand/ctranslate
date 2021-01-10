import os
import sys
import re
import mimetypes
import shutil
import datetime
import tempfile
from pathlib import Path
from ctrans.basefile import BaseFile
from ctrans.ctransfile import CTransFile
import trans.constants

class CTransManager:
    """CTranslation manager class"""

    def __init__(self, extention_list, replacedir_list):

        self.name = "CTranslation manager"

        # file extensions to be translated
        exts = []
        for each in extention_list:
            if len(each) > 0 and each[0] != '.':
                each = '.' + each
            exts.append(each)
        self.extentions = exts

        # replacement for directories (no error processing..)
        replace_dict = {}
        pattern = "^([^:]+):([^:]+)$"
        for each in replacedir_list:
            result = re.match(pattern, each)
            if result != None:
                replace_dict[result.group(1)] = result.group(2)
        self.replace_dict = replace_dict

    def create_ctransfiles(self, srcdir, outdir):

        self.srcdir = srcdir
        self.outdir = outdir

        for path in sorted(Path(srcdir).iterdir()):
            self.create_ctransfile(path, outdir)

    def create_ctransfile(self, inpath, outdir):

        # If inpath is a directory
        if inpath.is_dir():

            if inpath.name == outdir:
                return

            # Return if "dot" directory
            if inpath.name[0] == '.':
                return

            inpath_name = inpath.name
            for k, v in self.replace_dict.items():
                pattern = "^"+k+"$"
                result = re.match(pattern, inpath_name)
                if result != None:
                    inpath_name = inpath_name.replace(k, v)
            transdir = os.path.join(outdir, inpath_name)

            # Execute child paths recursively
            for child_path in sorted(inpath.iterdir()):
                self.create_ctransfile(child_path, transdir)

        # If inpath is a file (not a directory)
        else:

            type, subtype = mimetypes.guess_type(inpath, strict=True)
            if type in ctrans.constants.excl_list:
                return

            inpath_root, inpath_ext = os.path.splitext(inpath)
            if not inpath_ext in self.extentions:
                return

            os.makedirs(outdir, exist_ok=True)
            ctrans_path = os.path.join(outdir, inpath)
            if not os.path.isfile(ctrans_path):
                ctransfile = CTransFile()
                ctransfile.create(inpath, outdir)

    def create_ctranslation_files(self, srcdir, transdir, outdir):

        self.srcdir   = srcdir
        self.transdir = transdir
        self.outdir   = outdir

        exit_code = 0
        for child_path in sorted(Path(srcdir).iterdir()):
            flag = self.create_ctranslation_file(child_path, transdir, outdir)
            if flag == False:
                exit_code = 1

        return exit_code

    def create_ctranslation_file(self, srcpath, transdir, outdir):

        flag = True
        last_flag = True

        #print('srcpath: %s' % srcpath.absolute())

        # If srcpath is a directory
        if srcpath.is_dir():

            if srcpath.name == outdir:
                return last_flag

            # Return if "dot" directory
            if srcpath.name[0] == '.':
                return last_flag

            curr_transdir = os.path.join(transdir, srcpath.name)
            curr_outdir   = os.path.join(outdir,   srcpath.name)
            for k, v in self.replace_dict.items():
                pattern = "^"+k+"$"
                result = re.match(pattern, curr_transdir)
                if result != None:
                    curr_transdir = curr_transdir.replace(k, v)

            # Execute child paths recursively
            for child in sorted(Path(srcpath).iterdir()):
                flag = self.create_ctranslation_file(child, curr_transdir, curr_outdir)
                if flag == False:
                    last_flag = False

        # If path is a file (not a directory)
        else:

            type, subtype = mimetypes.guess_type(srcpath, strict=True)
            if type in ctrans.constants.excl_list:

                if self.filenewer2(srcpath, outdir):
                    self.copy2(srcpath, outdir)
                    print('Copied ' + srcpath.name + ' because of exclude_ext')
                return True

            transpath = os.path.join(transdir, srcpath.name + ctrans.constants.ctrans_ext)

            # If transdoc file not exist
            if not os.path.isfile(transpath):

                if self.filenewer2(srcpath, outdir):
                    self.copy2(srcpath, outdir)
                    print('Copied ' + srcpath.name + ' because of no ctrans file')

            else:
                if self.filenewer3(srcpath, transdir, outdir):
                    flag = self.output_ctranslation_file(srcpath, transdir, outdir)

                    if flag == True:
                        outpath = os.path.join(outdir, srcpath.name)
                    else:
                        last_flag = False

        return last_flag

    def filenewer2(self, srcpath, outdir):

        outpath = os.path.join(outdir, srcpath.name)
        if not os.path.isfile(outpath):
            return True

        mtime1 = os.path.getmtime(srcpath)
        mtime2 = os.path.getmtime(outpath)

        return mtime1 > mtime2

    def filenewer3(self, srcpath, transdir, outdir):

        transpath = os.path.join(transdir, srcpath.name + trans.constants.trans_ext)
        outpath = os.path.join(outdir, srcpath.name)

        if not os.path.isfile(outpath):
            return True

        mtime1 = os.path.getmtime(srcpath)
        mtime2 = os.path.getmtime(transpath)
        mtime3 = os.path.getmtime(outpath)

        return (mtime2 > mtime3) | (mtime1 > mtime3)

    def output_ctranslation_file(self, srcpath, transdir, outdir):

        srcfile = BaseFile()
        srcfile.open(srcpath, 'r')

        outpath = os.path.join(outdir, srcpath.name)
        if not os.path.isdir(outdir):
            os.makedirs(outdir, exist_ok=True)

        transpath = os.path.join(transdir, srcpath.name + trans.constants.trans_ext)
        ctransfile = CTransFile()
        ctransfile.open(transpath, 'r')

        outfile = BaseFile()
        outfile.open(outpath, 'w')
        flag = self.output_lines(srcfile, ctransfile, outfile)

        outfile.close()

        if flag != True:
            os.remove(outpath)
        ctransfile.close()
        srcfile.close()

        return flag

    def output_lines(self, srcfile, ctransfile, outfile):

        line_ctrans = ""
        dummy, start_token_pos = ctransfile.read_until_next_start_token()

        # If next start token position is not -1 (next start token found)
        if start_token_pos != -1:

            # Get first source part in transdoc file
            line_ctrans, err1 = ctransfile.get_current_line()

        # Get one line from source file
        line_src, err = srcfile.get_current_line()
        old_line_src_pos = srcfile.get_curr_line_num()

        # In case srcfile may have no contents
        if err == 1:
            return 0;

        error_not_occurred = True
        proc_continue = True
        src_retry = False
        while srcfile.get_curr_line_num() <= srcfile.get_line_count() and proc_continue:

            #print('old_line_src_pos    : %d' % old_line_src_pos, file=sys.stderr)
            #print('line_src   (l%d/E%d): %s' % (srcfile.get_curr_line_num(), err, line_src.rstrip('\n')), file=sys.stderr)
            #print('line_trans (l%d/E%d): %s' % (ctransfile.get_curr_line_num(), err1, line_ctrans.rstrip('\n')), file=sys.stderr)

            if err != 0: # or src_retry == True:
                if err1 == 0 and line_trans != "":
                    print("--------+-", file=sys.stderr)
                    print('Error: Source part in "%s" not matched.\n(L.%d) %s'
                          % (ctransfile.pathname, ctransfile.get_curr_line_num(), line_ctrans.rstrip('\n')),
                          file=sys.stderr)

                    # In case current ctrans line does not match any src line.
                    # So src line position set back next paragraph.
                    srcfile.set_line_num(old_line_src_pos)
                    line_src, err = srcfile.get_current_line()
                    old_line_src_pos = srcfile.get_curr_line_num()
                    line_src_list = []
                    line_src_list.append(line_src)

                    #print('line_src   (l%d/E%d): %s' % (srcfile.get_curr_line_num(), err, line_src.rstrip('\n')), file=sys.stderr)
                    #print('line_ctrans (l%d/E%d): %s' % (ctransfile.get_curr_line_num(), err1, line_ctrans.rstrip('\n')), file=sys.stderr)

                    pattern = "^$"
                    while True:
                        result = re.match(pattern, line_src)
                        if result == None: # and line_src != line_trans:
                            line_src, err = srcfile.get_current_line()
                            line_src_list.append(line_src)
                        else:
                            line_src_list.pop(-1)
                            break

                    old_line_src_pos = srcfile.get_curr_line_num()
                    if len(line_ctrans_list) == 0:
                        line_ctrans_list.append(line_trans)

                    # And also skip ctrans line to next start token
                    line_ctrans_skip, err2 = ctransfile.read_until_next_start_token()
                    line_ctrans, err1 = ctransfile.get_current_line()
                    line_ctrans_list.extend(line_ctrans_skip)

                    error_not_occurred = False
                    self.output_diff(srcfile, ctransfile, line_src_list, line_ctrans_list)
                    line_src_list = []
                    line_ctrans_list = []
                    proc_continue = True
                    src_retry = False
                    continue
                else:
                    #print('Unknown error', file=sys.stderr)
                    #print('line_src   (l%d/E%d): %s' % (srcfile.get_curr_line_num(), err, line_src.rstrip('\n')), file=sys.stderr)
                    #print('line_ctrans (l%d/E%d): %s' % (ctransfile.get_curr_line_num(), err1, line_ctrans.rstrip('\n')), file=sys.stderr)
                    break

            # In case source line in ctrans file did not exist in source file
            # and is not between ctrans tokens, it should be output as is.
            elif line_ctrans != "" and line_src != line_ctrans:
                outfile.add_line(line_src)
                line_src, err = srcfile.get_current_line()

            # In case source line in ctrans file existed in source file
            elif line_ctrans != "" and line_src == line_ctrans:

                line_src_list   = []
                line_ctrans_list = []
                line_src_list.append(line_src)
                line_ctrans_list.append(line_ctrans)

                while True:

                    line_src,   err   = srcfile.get_current_line()
                    line_ctrans, err1 = ctransfile.get_current_line()

                    line_src_list.append(line_src)
                    line_ctrans_list.append(line_ctrans)

                    #print('  line_src    (l%d/E%d): %s' % (srcfile.get_curr_line_num(), err, line_src.rstrip('\n')), file=sys.stderr)
                    #print('  line_ctrans (l%d/E%d): %s' % (ctransfile.get_curr_line_num(), err1, line_ctrans.rstrip('\n')), file=sys.stderr)

                    if line_src != line_ctrans:
                        len_token = len(ctrans.constants.ctrans_trans)

                        # If current line in ctrans file is ctrans_trans token
                        if len(line_ctrans)>=len_token and line_ctrans[0:len_token]==ctrans.constants.ctrans_trans:
                            old_line_src_pos = srcfile.get_curr_line_num()
                            break

                        else:
                            # Lines between source file and source part in ctrans file do not match
                            print("----------", file=sys.stderr)
                            print('Error: Source part in "%s" not matched.\n(L.%d) %s'
                                % (ctransfile.pathname, ctransfile.get_curr_line_num(), line_ctrans.rstrip('\n')),
                                file=sys.stderr)

                            # Skip ctransfile line to next token potision
                            # Also append lines to next token to line list for error (diff) message
                            line_ctrans_skip, err2 = ctransfile.read_until_next_start_token()
                            if len(line_ctrans_skip) != 0:
                                line_ctrans_list.extend(line_ctrans_skip)
                            line_ctrans, err1 = ctransfile.get_current_line()

                            line_src_list = self.get_srcs_when_error(srcfile, line_src, line_src_list)

                            error_not_occurred = False
                            self.output_diff(srcfile, ctransfile, line_src_list, line_ctrans_list)
                            proc_continue = True
                            break

                if proc_continue == False:
                    self.output_diff(srcfile, ctransfile, line_src_list, line_ctrans_list)
                    proc_continue = True

                else:
                    src_retry = False
                    len_end = len(ctrans.constants.ctrans_end)

                    # Output translation part of ctransfile into outfile
                    while True:

                        line_ctrans, err1 = ctransfile.get_current_line()
                        if err1 != 0:
                            break
                        elif len(line_ctrans)>=len_end and line_ctrans[0:len_end]==ctrans.constants.ctrans_end:
                            break
                        else:
                            outfile.add_line(line_ctrans)

                    old_ctrans_list = line_ctrans_list
                    # Proceed position of ctransfile to next start token
                    dummy, err1 = ctransfile.read_until_next_start_token()

                    if err1 != -1:
                        line_ctrans, err1 = ctransfile.get_current_line()
                        line_ctrans_list = []
                    else:
                        proc_continue = True

            elif len(line_src.rstrip('\n')) == 0 and len(line_ctrans.rstrip('\n')) == 0:
                return True

            elif err1 != 1:
                return False
            else:
                print("Unknown error", file=sys.stderr)
                print("srcfile: %s" % srcfile.pathname)
                print('line_src    (L.%d/E%d): |%s|' % (srcfile.get_curr_line_num(), err, line_src.rstrip('\n')), file=sys.stderr)
                print('line_ctrans (L.%d/E%d): |%s|' % (ctransfile.get_curr_line_num(), err1, line_ctrans.rstrip('\n')), file=sys.stderr)
                return False

        #if error_not_occurred == False:
        #    os.remove(outfile.pathname)
        return error_not_occurred

    def copy2(self, srcpath, outdir):

        outpath = os.path.join(outdir, srcpath.name)
        dir_and_base = os.path.split(outpath)
        dirname = dir_and_base[0]
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        shutil.copy(srcpath, outdir)

    def output_diff(self, srcfile, ctransfile, line_src_list, line_ctrans_list):

        tmpdir = tempfile.TemporaryDirectory()
        tmpname = tmpdir.name
        #tmpname = tempfile.mkdtemp()
        fp_src    = open(tmpname+'/src.txt', 'w', encoding='utf-8')
        fp_ctrans = open(tmpname+'/ctrans.txt', 'w', encoding='utf-8')

        for line_src in line_src_list:
            fp_src.write(line_src)
        for line_ctran in line_ctrans_list:
            fp_ctrans.write(line_ctran)
        fp_ctrans.close()
        fp_src.close()

        os.system("diff -au "+tmpname+"/ctrans.txt "+tmpname+"/src.txt > "+tmpname+"/diff.txt")
        t_src = os.path.getmtime(srcfile.pathname)
        d_src = str(datetime.datetime.fromtimestamp(t_src))
        t_ctrans = os.path.getmtime(ctransfile.pathname)
        d_ctrans = str(datetime.datetime.fromtimestamp(t_ctrans))
        s = "sed -i -e \"s|\-\-\- .*$|--- a/"+str(ctransfile.pathname)+"\t"+str(d_ctrans)+"|\" "
        s = s +    "-e \"s|+++ .*$|+++ b/"+str(srcfile.pathname)+"\t"+str(d_src)+"|\" "
        s = s + tmpname+"/diff.txt"
        os.system(s)
        fp_diff = open(tmpname+'/diff.txt', 'r', encoding='utf-8')
        lines_diff = fp_diff.readlines()
        print("Pseudo diff:", file=sys.stderr)
        for line_diff in lines_diff:
            print("%s" % line_diff.replace("\n",""), file=sys.stderr)

        fp_diff.close()
        tmpdir.cleanup()

    def get_srcs_when_error(self, srcfile, line_src, line_src_list):

        # Skip srcfile line to next non-blank line
        # Also append the line to list for error (diff) message
        pattern = "^$"
        while True:
            result = re.match(pattern, line_src)
            if result == None:
                line_src, err = srcfile.get_current_line()
                line_src_list.append(line_src)
            else:
                line_src_list.pop(-1)
                break
        return line_src_list
