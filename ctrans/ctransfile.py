import sys
import os
import re
from pathlib import Path
from ctrans.basefile import BaseFile
import ctrans.constants

class CTransFile(BaseFile):
    """A CTransation file class"""

    def __init__(self):
        super().__init__()
        self.name = "CTranslation file"
        self.current_pos = 0

    def create(self, src_path, out_dir):
        """Create CTranslation file."""

        self.pathname = os.path.join(out_dir, src_path.name + ctrans.constants.ctrans_ext)
        if os.path.isfile(self.pathname):
            return

        outstr = ""
        self.open(self.pathname, 'w')

        srcfile = BaseFile()
        srcfile.open(src_path, 'r')

        pattern = "^$"
        i=0
        first = True
        for line in srcfile.get_lines():
            result = re.match(pattern, line)
            if result:
                if outstr != "":
                    self.output(outstr, first)
                    outstr = ""
                    first = False
            else:
                outstr = outstr+ line
            i += 1

        if outstr != "":
            self.output(outstr, first)

        self.close()

    def output(self, line, flag):

        # Add \n if line has no \n at the end.
        if line[-1] != '\n':
            outstr = line + '\n'
        else:
            outstr = line

        if flag != True:
            self.add_line('\n')
        self.add_line(ctrans.constants.ctrans_start + '\n')
        self.add_line(outstr)
        self.add_line(ctrans.constants.ctrans_trans + '\n')
        self.add_line(outstr)
        self.add_line(ctrans.constants.ctrans_end   + '\n')

    def read_until_next_start_token(self):

        whole_count = self.get_line_count()

        if self.current_pos >= whole_count:
            return [], -1

        retline = []
        ret_flag = True
        len_start = len(ctrans.constants.ctrans_start)
        len_trans = len(ctrans.constants.ctrans_trans)

        while True:

            if self.current_pos < whole_count:

                #line, err = self.get_current_line()
                line = self.get_current_line()
                if self.is_error():
                    return retline, -1
                if len(line)>=len_trans and line[0:len_trans] == ctrans.constants.ctrans_trans:
                    ret_flag = False
                if ret_flag == True:
                    retline.append(line)
                if len(line)<len_start:
                    continue
                if line[0:len_start] == ctrans.constants.ctrans_start:
                    return retline, 0

            else:
                break

        return [], -1
