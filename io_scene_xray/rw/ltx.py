# standart modules
import os

# addon modules
from .. import log
from .. import text
from .. import utils


class _LtxSection:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.params = {}


class LtxParser:
    _WHITESPACE = {' ', '\t'}
    _COMMENT = {';', '/'}

    def __init__(self):
        self.path = ''
        self.sections = {}
        self.values = {}

    def from_file(self, path):
        self.path = path
        with open(self.path, 'r') as file:
            self._data = file.read()
        self._parse()

    def from_str(self, data):
        self._data = data
        self._parse()

    def _remove_spaces_and_comments(self):
        self._parsed_lines = []
        self._src_lines = {}
        line_index = 0

        for src_line_index, line in enumerate(self._data.splitlines()):
            char_index = 0
            char_count = len(line)
            parsed_line = ''

            while char_index < char_count:
                char = line[char_index]
                char_index += 1

                # save string
                if char == '"':
                    while char_index < char_count:
                        char = line[char_index]
                        char_index += 1
                        if char == '"':
                            break
                        parsed_line += char
                    continue

                if char in self._WHITESPACE:
                    continue

                if char in self._COMMENT:
                    break

                parsed_line += char

            if parsed_line:
                self._parsed_lines.append(parsed_line)
                self._src_lines[line_index] = (line, src_line_index)
                line_index += 1

    def _parse_sections(self, line):
        line = line[1 : ]    # cut "["

        # parse section header
        split_char = ']'
        if ':' in line:
            split_char += ':'
            section_name, section_parent = line.split(split_char)
        else:
            section_name = line.split(split_char)[0]
            section_parent = None

        section = _LtxSection(section_name, section_parent)
        self.sections[section_name] = section
        self._line_index += 1

        start_new_section = False
        while not start_new_section and self._line_index < self._lines_count:
            line = self._parsed_lines[self._line_index]

            if line.startswith('['):
                start_new_section = True

            else:
                # parse section params
                if '=' in line:
                    param_name, param_value = line.split('=')
                else:
                    param_name = line
                    param_value = None

                section.params[param_name] = param_value
                self._line_index += 1

    def _parse_fs(self, line):
        section = _LtxSection('root', None)
        self.sections['root'] = section
        prop_name, prop_value = line.split('=')
        line_parts = prop_value.split('|')
        parent_key = line_parts[2]

        if parent_key == '$fs_root$':
            fs_path = os.path.dirname(self.path).replace('\\', os.sep)
            self.values[prop_name] = fs_path

        elif parent_key.startswith('$') and parent_key.endswith('$'):
            if len(line_parts) > 3:
                parent = self.values[parent_key]
                value = line_parts[3]
                path = os.path.join(parent, value)
                path = path.replace('\\', os.sep)
                self.values[prop_name] = path

            else:
                self.values[prop_name] = self.values[parent_key]

        else:
            sdk_root = self.values.get('$sdk_root$', None)

            if sdk_root is None:
                utils.draw.show_message(
                    text.get_text(text.error.ltx_no_param),
                    ('$sdk_root$', ),
                    text.get_text(text.error.error_title),
                    'ERROR'
                )
                raise BaseException('error')

            value = os.path.join(sdk_root, parent_key)
            value = value.replace('\\', os.sep)
            self.values[prop_name] = value

        self._line_index += 1

    def _parse(self):
        self._remove_spaces_and_comments()
        self._line_index = 0
        self._lines_count = len(self._parsed_lines)

        while self._line_index < self._lines_count:
            line = self._parsed_lines[self._line_index]

            if line.startswith('['):
                self._parse_sections(line)

            elif line.startswith('$'):    # fs.ltx
                try:
                    self._parse_fs(line)
                except:
                    raise BaseException('error')

            elif line.startswith('#include'):
                self._line_index += 1

            else:
                src_line, src_index = self._src_lines[self._line_index]
                raise log.AppError('Line {}: {}'.format(src_index, src_line))
