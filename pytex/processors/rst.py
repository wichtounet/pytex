import os
import re

from collections import namedtuple

from base import Transformer

List = namedtuple("List", "depth type")
Style = namedtuple("Style", "rst_begin rst_end latex_begin latex_end")
Reference = namedtuple("Reference", "type title label")


class RstProcessor(Transformer):
    list_stack = []
    inside_frame = False
    references = []

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

    # Compute a label name
    def compute_label(self, type, title):
        source_base = os.path.basename(self.source)
        source_clean = source_base.replace(' ', '_')
        type_clean = type.replace(' ', '_')
        title_clean = title.replace(' ', '_')
        return source_clean + ":" + type_clean + ":" + title_clean

    # Add a new label
    def add_label(self, type, title):
        label = self.compute_label(type, title)

        self.print_line("\\label{" + label + "}")

        self.references.append(Reference(type, title, label))

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

        elif stripped.startswith('* '):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("* ", "", 1)

        elif stripped.startswith('+ '):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("+ ", "", 1)

        elif stripped.startswith('- '):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("- ", "", 1)

        elif line.startswith('  ') and self.list_stack and self.list_stack[-1].type == 1:
            # At this point, we consider a line starting with 3 spaces
            # as a continuation of the list
            return line

        elif line.startswith('   ') and self.list_stack and self.list_stack[-1].type == 2:
            # At this point, we consider a line starting with 3 spaces
            # as a continuation of the list
            return line

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
            self.print_line("\\begin{frame}[fragile]{" + title + "}")

            return True
        elif stripped.startswith('.. toc::'):
            toc_name = stripped.replace('.. toc::', "")
            toc_name = toc_name.strip()

            # By default full TOC is shown
            if not toc_name:
                toc_name = "main"

            if toc_name == "main":
                self.print_line("\\setcounter{tocdepth}{1}")
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[hidesubsections]")
                self.print_line("\\end{frame}")
                self.print_line("\\setcounter{tocdepth}{3}")
            elif toc_name == "current":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[currentsection,hideothersubsections]")
                self.print_line("\\end{frame}")
            elif toc_name == "currentsub":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\setcounter{tocdepth}{2}");
                self.print_line("\\tableofcontents[currentsection,hideothersubsections,currentsubsection,subsectionstyle=show/shaded/hide]")
                self.print_line("\\end{frame}")
            elif toc_name == "currentsubdeep":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\setcounter{tocdepth}{3}");
                self.print_line("\\tableofcontents[currentsection,hideothersubsections,currentsubsection,subsectionstyle=show/shaded/hide]")
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
        elif stripped.startswith('\\backupend') or stripped.startswith('\\backupbegin'):
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

    # Handle todo notes
    def handle_todo(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. todo:: '):
            note = stripped.replace('.. todo:: ', "")

            self.print_line("\\todo[inline]{" + note + "}")

            return True

        return False

    # Handle links
    def handle_links(self, line):
        first_index = 0

        rst_begin = "`"
        rst_end = "`_"

        while first_index < len(line):
            begin = line.find(rst_begin, first_index)

            if begin == -1:
                break

            end = line.find(rst_end, begin + len(rst_begin))

            if end == -1:
                break

            length = end - begin

            first_index = begin

            if length > len(rst_begin):
                title = line[begin+len(rst_begin):end]

                count = 0
                for ref in self.references:
                    if ref.title == title:
                        count = count + 1

                if count == 0:
                    self.logger.info("Invalid reference {}".format(title))
                    first_index = end
                    line = line[:begin] + title + line[end+len(rst_end):]
                elif count > 1:
                    self.logger.info("Ambiguous reference {}".format(title))
                    first_index = end
                    line = line[:begin] + title + line[end+len(rst_end):]
                else:
                    for ref in self.references:
                        if ref.title == title:
                            if ref.type == "chapter":
                                replacement = "Chapter~\\ref{"
                            else:
                                replacement = "Section~\\ref{"

                            replacement = replacement + ref.label + "}"

                            break

                    line = line[:begin] + \
                        replacement + \
                        line[end+len(rst_end):]

                    first_index = begin - len(rst_begin) - len(rst_end) + len(replacement)
            else:
                first_index = end

        return line

    # Handle all styles
    def handle_styles(self, line):
        styles = []
        styles.append(Style(":code:`", "`", "\\cppi{", "}"))
        styles.append(Style(":math:`", "`", "$", "$"))
        styles.append(Style("**", "**", "\\textbf{", "}"))
        styles.append(Style("*", "*", "\\textit{", "}"))
        styles.append(Style("|", "|", "\\gls{", "}"))

        # Handle citations
        if "nobiblatex" in self.options:
            styles.append(Style("[", "]_", "\\cite{", "}"))
        else:
            styles.append(Style("[", "]_", "\\autocite{", "}"))

        min_style = styles[0]

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

            rst_begin = min_style.rst_begin
            rst_end = min_style.rst_end
            latex_begin = min_style.latex_begin
            latex_end = min_style.latex_end

            first_index = min
            second_index = line.find(rst_end, first_index+len(rst_begin))

            # Handle plural acronym
            if rst_begin == "|" and line[second_index - 1] == 's':
                second_index = second_index - 1
                rst_end = "s|"
                latex_begin = "\\glspl{"

            line = line[:first_index] + \
                latex_begin + \
                line[first_index+len(rst_begin):second_index] + \
                latex_end + \
                line[second_index+len(rst_end):]

            first_index = first_index - len(rst_begin) - len(rst_end) + len(latex_begin) + len(latex_end) + (second_index - first_index)

        return line

    # Clean a final line
    def clean_line(self, line):
        if "nobiblatex" in self.options:
            # 1. Merge multiple cite together
            check = True
            while check:
                cleaned_line = re.sub(r"\\cite\{([a-zA-Z0-9,]*)\}[\s]*\\cite\{([a-zA-Z0-9,]*)\}", r"\\cite{\1,\2}", line)
                check = cleaned_line != line
                line = cleaned_line

            # 2. Adds a insecable space in front of cite
            cleaned_line = re.sub(r"\\cite\{([a-zA-Z0-9,]*)\}", r"~\\cite{\1}", line)
            line = cleaned_line

            return cleaned_line
        else:
            # 1. Merge multiple autocite together
            check = True
            while check:
                cleaned_line = re.sub(r"\\autocite\{([a-zA-Z0-9,]*)\}[\s]*\\autocite\{([a-zA-Z0-9,]*)\}", r"\\autocite{\1,\2}", line)
                check = cleaned_line != line
                line = cleaned_line

            # 2. Adds a insecable space in front of autocite
            cleaned_line = re.sub(r"\\autocite\{([a-zA-Z0-9,]*)\}", r"~\\autocite{\1}", line)
            line = cleaned_line

            return cleaned_line

    # Final cleanup
    def final_cleanup(self, lines):
        composed_line = ""
        ignored = False

        for line in lines:
            if "__rst_ignore__" in line:
                ignored = not ignored
                self.print_line(line)
                continue

            if ignored:
                self.print_line(line)
                continue

            # If the line starts with a command, we don't compose it
            if len(line) > 0 and line.startswith("\\"):
                if len(composed_line) > 0:
                    self.print_line(self.clean_line(composed_line))
                    composed_line = ""

                self.print_line(self.clean_line(line))

                continue

            # An empty line is the end of a paragraph
            if len(line) == 0:
                if len(composed_line) > 0:
                    self.print_line(self.clean_line(composed_line))
                composed_line = ""
                self.print_line(line)
            else:
                if len(composed_line) > 0:
                    composed_line = composed_line + " " + line
                else:
                    composed_line = line

        if len(composed_line) > 0:
            self.print_line(self.clean_line(composed_line))

    def auto_ignore_env(self, env):
        if env == "figure":
            return True

        if env == "table":
            return True

        if env == "algorithm":
            return True

        if env == "algorithmic":
            return True

        return False

    # auto ignore some lines
    def auto_ignore(self, lines):
        ignored = False
        env_ignored = False

        for line in lines:
            if "__rst_ignore__" in line:
                ignored = not ignored
                self.print_line(line)
                continue

            if ignored:
                self.print_line(line)
                continue

            stripped = line.rstrip()

            if env_ignored:
                if stripped.startswith("\\end{") and stripped.endswith("}"):
                    new_env = stripped.replace("\\end{","")
                    new_env = new_env.replace("}", "")

                    if new_env == env:
                        env_ignored = False
                        self.print_line(line)
                        self.print_line("%__rst_ignore__")
                    else:
                        self.print_line(line)
                else:
                        self.print_line(line)

                continue

            if stripped.startswith("\\begin{") and stripped.endswith("}"):
                env = stripped.replace("\\begin{","")
                env = env.replace("}", "")

                if self.auto_ignore_env(env):
                    self.print_line("%__rst_ignore__")
                    self.print_line(line)
                    env_ignored = True
                else:
                    self.print_line(line)
            else:
                self.print_line(line)

    # Handle options
    def handle_options(self, lines):
        for line in lines:
            stripped = line.rstrip()

            if stripped.startswith(':Parameter '):
                option = stripped.replace(':Parameter ', "")
                option = option.strip()

                if option == "chapter:":
                    self.options.append("chapter")
                elif option == "nobiblatex:":
                    self.options.append("nobiblatex")
            else:
                self.print_line(line)

    # End code block
    def end_code(self):
        self.inside_code = False
        self.print_line("\\end{" + self.code + "code}")

        if self.listing:
            if len(self.listing_caption) > 0:
                self.print_line("\\caption{" + self.listing_caption + "}")

            if len(self.listing_label) > 0:
                self.print_line("\\label{" + self.listing_label + "}")

            self.listing_caption = ""
            self.listing_label = ""
            self.listing = False

            self.print_line("\\end{listing}")

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
        elif stripped.startswith('.. listing:: '):
            if self.inside_code:
                self.end_code()

            self.code = stripped.replace('.. listing:: ', "").strip()
            self.listing = True
            self.listing_caption = ""
            self.listing_label = ""

            if not self.code:
                self.code = "cpp"

            self.inside_code = True

            self.print_line("%__rst_ignore__")
            self.print_line("\\begin{listing}")
            self.print_line("\\begin{" + self.code + "code}")

            # The line is consumed
            return True
        elif self.inside_code and len(stripped) > 0 and not stripped.startswith('  '):
            self.end_code()

            # We do not consume this line
            return False
        elif self.inside_code:
            if self.listing and line.startswith('   :caption:'):
                self.listing_caption = line.replace('   :caption: ', "")
                return True

            if self.listing and line.startswith('   :label:'):
                self.listing_label = line.replace('   :label: ', "")
                return True

            # The line is printed and then consumed
            self.print_line(line)
            return True
        else:
            # We do not consume this line
            return False

    # End math block
    def end_splitmath(self):
        self.inside_splitmath = False
        self.print_line("\\end{split}")
        self.print_line("\\end{align}")
        self.print_line("%__rst_ignore__")

    # Handle math directive
    def handle_splitmath(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. splitmath::'):
            if self.inside_splitmath:
                self.end_splitmath()

            self.inside_splitmath = True

            self.print_line("%__rst_ignore__")
            self.print_line("\\begin{align}")
            self.print_line("\\begin{split}")

            # The line is consumed
            return True
        elif self.inside_splitmath and not stripped.startswith('  '):
            self.end_splitmath()

            # We do not consume this line
            return False
        elif self.inside_splitmath:
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
        self.inside_splitmath = False
        self.listing = False

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

            # Handle math directives
            if self.handle_splitmath(line):
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

            # Handle todo notes
            if self.handle_todo(line):
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
                if char in ('#', '-', '_', '*', '+', '='):
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
                            self.add_label("chapter", title);
                        elif index is 1:
                            self.print_line("\section{" + title + "}")
                            self.add_label("section", title);
                        elif index is 2:
                            self.print_line("\subsection{" + title + "}")
                            self.add_label("subsection", title);
                        elif index is 3:
                            self.print_line("\subsubsection{" + title + "}")
                            self.add_label("subsubsection", title);
                        else:
                            self.print_line("Section too deep:" + title)
                    else:
                        if index is 0:
                            self.print_line("\section{" + title + "}")
                            self.add_label("section", title);
                        elif index is 1:
                            self.print_line("\subsection{" + title + "}")
                            self.add_label("subsection", title);
                        elif index is 2:
                            self.print_line("\subsubsection{" + title + "}")
                            self.add_label("subsubsection", title);
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

    STEP_AUTO_IGNORE = 0
    STEP_OPTIONS = STEP_AUTO_IGNORE + 1
    STEP_SECTIONS = STEP_OPTIONS + 1
    STEP_DIRECTIVES = STEP_SECTIONS + 1
    STEP_LISTS = STEP_DIRECTIVES + 1
    STEP_LINKS = STEP_LISTS + 1
    STEP_STYLES = STEP_LINKS + 1
    STEP_CLEAN = STEP_STYLES + 1
    STEPS = STEP_CLEAN

    # Process a single file
    def process_lines(self, lines, step):
        ignored = False

        # Ignore some lines
        if step is self.STEP_AUTO_IGNORE:
            self.auto_ignore(lines)

            return True

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

        # Handle line-wise steps
        if step < self.STEP_CLEAN:
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

                # Handle links
                if step is self.STEP_LINKS:
                    self.print_line(self.handle_links(line))

                # Handle styles
                if step is self.STEP_STYLES:
                    self.print_line(self.handle_styles(line))

        # Final cleanup
        if step is self.STEP_CLEAN:
            self.final_cleanup(lines)

        return step < self.STEPS
