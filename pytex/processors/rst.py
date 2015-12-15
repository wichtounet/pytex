from collections import namedtuple

from base import Transformer

List = namedtuple("List", "depth type")
Style = namedtuple("Style", "rst_begin rst_end latex_begin latex_end")


class RstProcessor(Transformer):
    list_stack = []
    inside_frame = False

    options = []

    name = "RestructuredText processor"

    # Indicates if the processor wants to proces the given file or not
    def wants(self, source):
        return source.endswith('.tex.rst')

    # Get the target file name
    def target(self, source):
        return source.replace('.tex.rst', '.tex')

    # Checks that no list is still open
    def end(self):
        if self.list_stack:
            while self.list_stack:
                self.end_list()

    # start a list
    def start_list(self, depth, type):
        self.list_stack.append(List(depth, type))

        if type == 1:
            self.print_line("\\begin{itemize}")
        elif type == 2:
            self.print_line("\\begin{enumerate}")

    # end the previous list
    def end_list(self):
        prev = self.list_stack[-1]

        if prev.type == 1:
            self.print_line("\\end{itemize}")
        elif prev.type == 2:
            self.print_line("\\end{enumerate}")

        self.list_stack.pop()

    # Handle a list item
    def handle_item(self, depth, type):
        if self.list_stack:
            prev = self.list_stack[-1]

            if prev.type == type:
                if prev.depth < depth:
                    self.start_list(depth, type)
                else:
                    while prev.depth > depth:
                        self.end_list()

                        if not self.list_stack:
                            break

                        prev = self.list_stack[-1]

                    if not self.list_stack:
                        self.start_list(depth, type)

            else:
                if prev.depth == depth:
                    self.end_list()
                    self.start_list(depth, type)
                elif prev.depth < depth:
                    self.start_list(depth, type)
                else:
                    while prev.depth > depth:
                        self.end_list()

                        if not self.list_stack:
                            break

                        prev = self.list_stack[-1]

                    if not self.list_stack:
                        self.start_list(depth, type)

        else:
            self.start_list(depth, type)

    # Handle lists
    def handle_lists(self, line):
        stripped = line.lstrip()

        # Compute the depth of the list based on the number of spaces
        # before the start character
        depth = len(line) - len(stripped)

        if stripped.startswith('1.'):
            self.handle_item(depth, 2)

            return "\item " + stripped.replace("1.", "", 1)

        elif stripped.startswith('*'):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("*", "", 1)

        elif stripped.startswith('+'):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("+", "", 1)

        elif stripped.startswith('-'):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("-", "", 1)

        else:
            while self.list_stack:
                self.end_list()

            return line

    # End frame
    def end_frame(self):
        if self.inside_frame:
            self.print_line("\\end{frame}")
            self.inside_frame = False

    # Handle frames
    def handle_frames(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. frame:: '):
            self.end_frame()

            frame_name = stripped.replace('.. frame:: ', "")
            title = self.latex_escape(frame_name)
            self.inside_frame = True

            self.print_line("\\begin{frame}[fragile]{" + title + "}")

            return True
        elif stripped.startswith('.. sframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. sframe:: ', "")
            title = self.latex_escape(frame_name)
            self.inside_frame = True

            self.print_line("\section{" + title + "}")
            self.print_line("\\begin{frame}[fragile]{" + title + "}")

            return True
        elif stripped.startswith('.. ssframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. ssframe:: ', "")
            title = self.latex_escape(frame_name)
            self.inside_frame = True

            self.print_line("\subsection{" + title + "}")
            self.print_line("\\begin{frame}[fragile]{" + title + "}")

            return True
        elif stripped.startswith('.. suframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. suframe:: ', "")
            title = self.latex_escape(frame_name)
            self.inside_frame = True

            self.print_line("\section*{" + title + "}")
            self.print_line("\\begin{frame}[fragile]{" + title + "}")

            return True
        elif stripped.startswith('.. ssuframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. ssuframe:: ', "")
            title = self.latex_escape(frame_name)
            self.inside_frame = True

            self.print_line("\subsection*{" + title + "}")
            self.print_line("\\begin{frame}[fragile]{" + frame_name + "}")

            return True
        elif stripped.startswith('.. toc::'):
            toc_name = stripped.replace('.. toc::', "")
            toc_name = toc_name.strip()

            # By default full TOC is shown
            if not toc_name:
                toc_name = "main"

            if toc_name == "main":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[hidesubsections]")
                self.print_line("\\end{frame}")
            elif toc_name == "current":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[currentsection,hideothersubsections]")
                self.print_line("\\end{frame}")
            elif toc_name == "shallow":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\begingroup");
                self.print_line("\\setcounter{tocdepth}{1}");
                self.print_line("\\tableofcontents[currentsection]");
                self.print_line("\\endgroup");
                self.print_line("\\end{frame}")
            elif toc_name == "multicol":
                self.print_line("\\begin{frame}[c]{Table of Contents}")
                self.print_line("\\centering")
                self.print_line("\\begin{columns}")
                self.print_line("\\begin{column}{0.4\\textwidth}")
                self.print_line("\\begingroup");
                self.print_line("\\setcounter{tocdepth}{1}");
                self.print_line("\\tableofcontents[currentsection]");
                self.print_line("\\endgroup");
                self.print_line("\\end{column}")
                self.print_line("\\begin{column}{0.4\\textwidth}")
                self.print_line("\\begingroup");
                self.print_line("\\setcounter{tocdepth}{2}");
                self.print_line("\\tableofcontents[currentsection,hideothersubsections,sectionstyle=show/hide]");
                self.print_line("\\endgroup");
                self.print_line("\\end{column}")
                self.print_line("\\end{columns}")
                self.print_line("\\end{frame}")

            return True
        elif stripped.startswith('\end{document}'):
            self.end_frame()
            self.print_line(line)
            return True
        elif stripped.startswith('\section'):
            self.end_frame()
            self.print_line(line)
            return True
        elif stripped.startswith('\subsection'):
            self.end_frame()
            self.print_line(line)
            return True
        elif stripped.startswith('\subsubsection'):
            self.end_frame()
            self.print_line(line)
            return True

        return False

    # Handle images
    def handle_images(self, lines, i):
        line = lines[i]
        stripped = line.rstrip()

        if stripped.startswith('.. image:: '):
            path = stripped.replace('.. image:: ', "")

            caption = False
            label = False
            center = False
            factor = ""

            n = 1
            while True:
                if lines[i + n].startswith('   :factor: '):
                    factor = lines[i + n].replace('   :factor: ', "")
                    n += 1
                elif lines[i + n].startswith('   :center:'):
                    center = True
                    n += 1
                elif lines[i + n].startswith('   :label:'):
                    label = True
                    label_str = lines[i + n].replace('   :label: ', "")
                    n += 1
                elif lines[i + n].startswith('   :caption:'):
                    caption = True
                    caption_str = lines[i + n].replace('   :caption: ', "")
                    n += 1
                else:
                    break

            figure = caption or label

            if figure:
                self.print_line("\\begin{figure}")

            if center:
                self.print_line("\center")

            self.print_line("\includegraphics[width=" + factor + "\\textwidth]{" + path + "}")

            if caption:
                self.print_line("\caption{" + caption_str + "}")

            if label:
                self.print_line("\label{" + label_str + "}")

            if figure:
                self.print_line("\\end{figure}")

            return [True, n - 1]

        return [False, 0]

    # Handle blocks
    def handle_blocks(self, lines, i):
        line = lines[i]
        stripped = line.rstrip()

        if stripped.startswith('.. block:: '):
            text = stripped.replace('.. block:: ', "")

            title = "Definition"

            n = 1
            while True:
                if lines[i + n].startswith('   :title: '):
                    title = lines[i + n].replace('   :title: ', "")
                    n += 1
                else:
                    break

            self.print_line("\\begin{block}{" + title + "}")
            self.print_line(text)
            self.print_line("\\end{block}")

            return [True, n - 1]

        return [False, 0]

    # Handle all styles
    def handle_styles(self, line):
        styles = []
        styles.append(Style(":code:`", "`", "\\cppi{", "}"))
        styles.append(Style(":math:`", "`", "$", "$"))
        styles.append(Style("**", "**", "\\textbf{", "}"))
        styles.append(Style("*", "*", "\\textit{", "}"))
        styles.append(Style("[", "]_", "\\autocite{", "}"))
        styles.append(Style("|", "|", "\\gls{", "}"))

        first_index = 0

        while first_index < len(line):
            min = -1
            for style in styles:
                begin = line.find(style.rst_begin, first_index)

                if begin == -1:
                    continue

                end = line.find(style.rst_end, begin + len(style.rst_begin))

                if end == -1:
                    continue

                length = end - begin

                if length > len(style.rst_begin) and (begin < min or min == -1):
                    min = begin
                    min_style = style

            if min < 0:
                break

            first_index = min
            second_index = line.find(min_style.rst_end, first_index+len(min_style.rst_begin))

            line = line[:first_index] + \
                min_style.latex_begin + \
                line[first_index+len(min_style.rst_begin):second_index] + \
                min_style.latex_end + \
                line[second_index+len(min_style.rst_end):]

            first_index = first_index - len(min_style.rst_begin) - len(min_style.rst_end) + len(min_style.latex_begin) + len(min_style.latex_end) + (second_index - first_index)

        return line

    # Handle options
    def handle_options(self, lines):
        for line in lines:
            stripped = line.rstrip()

            if stripped.startswith(':Parameter '):
                option = stripped.replace(':Parameter ', "")
                option = option.strip()

                if option == "chapter:":
                    self.options.append("chapter")
            else:
                self.print_line(line)

    # End code block
    def end_code(self):
        self.inside_code = False
        self.print_line("\\end{" + self.code + "code}")
        self.print_line("%__rst_ignore__")

    # Handle code directive
    def handle_code(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. code:: '):
            if self.inside_code:
                self.end_code()

            self.code = stripped.replace('.. code:: ', "").strip()

            if not self.code:
                self.code = "cpp"

            self.inside_code = True

            self.print_line("%__rst_ignore__")
            self.print_line("\\begin{" + self.code + "code}")

            # The line is consumed
            return True
        elif self.inside_code and len(stripped) > 0 and not stripped.startswith('  '):
            self.end_code()

            # We do not consume this line
            return False
        elif self.inside_code:
            # The line is printed and then consumed
            self.print_line(line)
            return True
        else:
            # We do not consume this line
            return False

    # End math block
    def end_math(self):
        self.inside_math = False
        self.print_line("\\end{align}")
        self.print_line("%__rst_ignore__")

    # Handle math directive
    def handle_math(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. math::'):
            if self.inside_math:
                self.end_math()

            self.inside_math = True

            self.print_line("%__rst_ignore__")
            self.print_line("\\begin{align}")

            # The line is consumed
            return True
        elif self.inside_math and not stripped.startswith('  '):
            self.end_math()

            # We do not consume this line
            return False
        elif self.inside_math:
            # The line is printed and then consumed
            self.print_line(line)
            return True
        else:
            # We do not consume this line
            return False

    # Handle directives
    def handle_directives(self, lines):
        self.inside_code = False
        self.inside_math = False

        n = len(lines)
        i = 0

        while i < n:
            line = lines[i]

            # Handle code directives
            if self.handle_code(line):
                i += 1
                continue

            # Handle math directives
            if self.handle_math(line):
                i += 1
                continue

            # Handle frames
            if self.handle_frames(line):
                i += 1
                continue

            # Handle images
            ret_images, inc_images = self.handle_images(lines, i)
            if ret_images:
                i += inc_images
                i += 1
                continue

            # Handle blocks
            ret_blocks, inc_blocks = self.handle_blocks(lines, i)
            if ret_blocks:
                i += inc_blocks
                i += 1
                continue

            # Finaly, filter comments
            if not line.strip().startswith('.. '):
                self.print_line(line)

            i += 1

    def latex_escape(self, value):
        return value.replace('_', '\_')

    # Handle sections
    def handle_sections(self, lines):
        levels = []

        ignored = False

        for i in range(len(lines) - 1):
            first_line = lines[i]
            second_line = lines[i+1]

            if "__rst_ignore__" in first_line:
                ignored = not ignored
                self.print_line(first_line)
                continue

            if ignored:
                self.print_line(first_line)
                continue

            if len(first_line) > 0 and len(second_line) > 0:
                c = 0
                char = second_line[0]
                if char in ('#', '-', '_', '*', '+'):
                    while c < len(second_line) and second_line[c] is char:
                        c = c + 1

                if c >= 3 and c <= len(first_line):
                    if char not in levels:
                        levels.append(char)

                    index = levels.index(char)
                    title = self.latex_escape(first_line)

                    if "chapter" in self.options:
                        if index is 0:
                            self.print_line("\chapter{" + title + "}")
                        elif index is 1:
                            self.print_line("\section{" + title + "}")
                        elif index is 2:
                            self.print_line("\subsection{" + title + "}")
                        elif index is 3:
                            self.print_line("\subsubsection{" + title + "}")
                        else:
                            self.print_line("Section too deep:" + title)
                    else:
                        if index is 0:
                            self.print_line("\section{" + title + "}")
                        elif index is 1:
                            self.print_line("\subsection{" + title + "}")
                        elif index is 2:
                            self.print_line("\subsubsection{" + title + "}")
                        else:
                            self.print_line("Section too deep:" + first_line)

                    lines[i+1] = ""
                else:
                    self.print_line(first_line)
            else:
                self.print_line(first_line)

        if len(lines) > 0:
            # Print the very last line
            self.print_line(lines[len(lines) - 1])

    STEP_OPTIONS = 0
    STEP_SECTIONS = STEP_OPTIONS + 1
    STEP_DIRECTIVES = STEP_SECTIONS + 1
    STEP_LISTS = STEP_DIRECTIVES + 1
    STEP_STYLES = STEP_LISTS + 1
    STEPS = STEP_STYLES

    # Process a single file
    def process_lines(self, lines, step):
        ignored = False

        # Handle options
        if step is self.STEP_OPTIONS:
            self.handle_options(lines)

            return True

        # Handle sections
        if step is self.STEP_SECTIONS:
            self.handle_sections(lines)

            return True

        # Handle directives
        if step is self.STEP_DIRECTIVES:
            self.handle_directives(lines)

            return True

        for line in lines:
            if "__rst_ignore__" in line:
                ignored = not ignored
                self.print_line(line)
                continue

            if ignored:
                self.print_line(line)
                continue

            # Handle lists
            if step is self.STEP_LISTS:
                self.print_line(self.handle_lists(line))

            # Handle styles
            if step is self.STEP_STYLES:
                self.print_line(self.handle_styles(line))

        return step < self.STEPS
