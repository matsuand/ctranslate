class BaseFile:
    """A base file class"""

    def __init__(self):
        self.name     = ""
        self.pathname = ""
        self.curr_line_num = 0
        self.lines = []
        self.fo = None
        self.filemode = ''

    def open(self, pathname, mode):

        self.pathname = pathname
        self.filemode = mode

        if mode == 'r':
            self.fo = open(pathname, mode, encoding='utf-8')
            self.lines = self.fo.readlines()
        elif mode == 'w':
            self.fo = open(pathname, mode)

    def close(self):

        if self.filemode == 'w':
            self.fo.writelines(self.lines)
        self.fo.close()

    def getline(self, cnt):

        return self.lines[cnt]

    def getline_with_pos(self, cnt):

        line = self.lines[cnt]
        curr_line_num = cnt
        return line

    def get_current_line(self):

        if self.curr_line_num >= self.get_line_count():
            return "", 1

        line = self.lines[self.curr_line_num]
        if line[-1] != '\n':
            line = line + '\n'
        self.curr_line_num += 1
        return line, 0

    def get_lines(self):

        return self.lines

    def get_line_count(self):

        return len(self.lines)

    def add_line(self, line):

        self.lines.append(line)

    def get_curr_line_num(self):

        return self.curr_line_num

    def set_line_num(self, pos):

        self.curr_line_num = pos
