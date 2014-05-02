import os
import re
import sys
import curses

from pytex.subcommands import Command
from pytex.utils import find_files_of_type


class FindUnreferencedAcronyms(Command):

    name = 'checkacronyms', 'ca'
    acronym_regex = r'([A-Z]+-[A-Z]+|[A-Z]{2,})[a-z]*'

    def parser(self):
        parser = self.parser_class()
        parser.add_argument('files', nargs='*')
        return parser

    def execute(self, args):
        files = args.files

        if not files:
            files = find_files_of_type(os.path.realpath('.'), 'tex')

        stdscr = curses.initscr()
        curses.savetty()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        for f in files:
            with open(f) as fh:
                self.replacements = []
                contents = fh.read()
                for m in re.finditer(self.acronym_regex, contents):
                    ms, me = m.start(), m.end()
                    token = contents

                    line = contents.count("\n", 0, ms)

                    min_context = 10
                    max_context = 500

                    # Isolate a single line
                    cs = contents.rfind("\n", 0, ms) + 1
                    ce = contents.find("\n", me)

                    char = ms - cs

                    ms -= cs
                    me -= cs
                    token = token[cs:ce]

                    # For long lines, enforce max context
                    #cs = max(0, ms - max_context)
                    #ce = min(len(token), me + max_context)

                    # Find a whitespace to split on, if not found, take the extremes
                    #cs = token.find(" ", cs, max(0, ms - min_context)) + 1
                    #ce = token.rfind(" ", me + min_context, ce)
                    #if ce < 0:
                    #    ce = min(len(token), me + max_context)

                    #ms -= cs
                    #me -= cs
                    #token = token[cs:ce]

                    self.print_token_color(stdscr, f, token, line, char, ms, me)

                    callbacks = {
                        'l': self.replace_lower,
                        'u': self.replace_upper,
                        'p': self.replace_lower_plural,
                        'j': self.replace_upper_plural,
                    }

                    try:
                        c = stdscr.getch()
                        try:
                            callback = callbacks[chr(c)]
                        except (KeyError, ValueError):
                            if c == ord('f'):
                                break
                            else:
                                continue
                        else:
                            callback(contents, m.start(), m.end())
                    except KeyboardInterrupt:
                        curses.resetty()
                        curses.nocbreak()
                        curses.echo()
                        curses.endwin()
                        return

            if self.replacements:
                for s, e, string in reversed(self.replacements):
                    contents = contents[:s] + string + contents[e:]
                with open(f, 'w') as fh:
                    fh.write(contents)


    def replace_lower(self, content, start, end):
        self.replacements.append((
            start, end,
            '\\gls{{{}}}'.format(content[start:end].lower())
        ))

    def replace_upper(self, content, start, end):
        self.replacements.append((
            start, end,
            '\\Gls{{{}}}'.format(content[start:end].lower())
        ))


    def replace_lower_plural(self, content, start, end):
        name = content[start:end]
        if name.endswith('s'):
            name = name[:-1]
        self.replacements.append((
            start, end,
            '\\glspl{{{}}}'.format(name.lower())
        ))


    def replace_upper_plural(self, content, start, end):
        self.replacements.append((
            start, end,
            '\\Glspl{{{}}}'.format(content[start:end].lower())
        ))


    def print_token_color(self, stdscr, path, token, line, char, start, end):
        prefix = ':{}:{}-{}'.format(line + 1, char + 1, char + end - start)
        abbr = token[start:end]

        stdscr.erase()
        stdscr.addstr(1, 5, path+prefix)
        prefix=''

        chunksize = 80
        line = 0

        while token:
            chunk, token = token[:chunksize], token[chunksize:]
            stdscr.addstr(3 + line, 5, chunk)
            if start > chunksize:
                start -= chunksize
            elif start is not None:
                stdscr.addstr(3 + line, 5 + start, abbr, curses.A_UNDERLINE | curses.A_BOLD)
                start = None

            line += 1

        #try:
        #
        #except curses.error:
        #   pass
        stdscr.refresh()


    def print_token_plain(self, stdscr, token, line, char, start, end):
        prefix = '{}:{}-{} - '.format(line + 1, char + 1, char + end - start)

        print('{}{}'.format(
            prefix,
            token
        ))
        print(' ' * (len(prefix) + start) + '^' * (end - start))


checkacronyms = FindUnreferencedAcronyms()
