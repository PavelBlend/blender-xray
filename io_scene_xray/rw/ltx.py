# standart modules
import os


class LtxSection:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.params = {}


class LtxParser:
    WHITESPACE = {' ', '\t'}
    COMMENT = {';', '/'}

    def from_file(self, path):
        self.path = path
        with open(self.path, 'r') as file:
            self.data = file.read()
        self.parse()

    def from_str(self, data):
        self.path = ''
        self.data = data
        self.parse()

    def remove_spaces_and_comments(self):
        self.parsed_lines = []

        for line in self.data.splitlines():
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

                if char in self.WHITESPACE:
                    continue

                if char in self.COMMENT:
                    break

                parsed_line += char

            if parsed_line:
                self.parsed_lines.append(parsed_line)

    def parse_sections(self, line):
        line = line[1 : ]    # cut "["

        # parse section header
        split_char = ']'
        if ':' in line:
            split_char += ':'
            section_name, section_parent = line.split(split_char)
        else:
            section_name = line.split(split_char)[0]
            section_parent = None

        section = LtxSection(section_name, section_parent)
        self.sections[section_name] = section
        self.line_index += 1

        start_new_section = False
        while not start_new_section and self.line_index < self.lines_count:
            line = self.parsed_lines[self.line_index]

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
                self.line_index += 1

    def parse_fs(self, line):
        section = LtxSection('root', None)
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
            value = os.path.join(self.values['$sdk_root$'], parent_key)
            value = value.replace('\\', os.sep)
            self.values[prop_name] = value

        self.line_index += 1

    def parse(self):
        self.remove_spaces_and_comments()
        self.line_index = 0
        self.lines_count = len(self.parsed_lines)
        self.sections = {}
        self.values = {}

        while self.line_index < self.lines_count:
            line = self.parsed_lines[self.line_index]

            if line.startswith('['):
                self.parse_sections(line)

            elif line.startswith('$'):    # fs.ltx
                self.parse_fs(line)

            elif line.startswith('#include'):
                self.line_index += 1

            else:
                raise BaseException(f'Invalid *.ltx syntax: {line}')
