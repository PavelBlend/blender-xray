import os


class StalkerLtxParser:
    WHITESPACE = {' ', '\t'}
    COMMENT = {';', '/'}

    class LtxSection:
        def __init__(self, name, parent):
            self.name = name
            self.parent = parent
            self.params = {}

    def __init__(self, path):
        self.path = path
        file = open(self.path, 'r')
        self.data = file.read()
        file.close()
        self.parse()

    def parse(self):
        parse_lines = []
        for line in self.data.split('\n'):
            if line.count('"') > 2:
                raise BaseException('Invalid *.ltx syntax')
            parse_line = ''
            char_index = 0
            char_count = len(line)
            while char_index < char_count:
                char = line[char_index]
                char_index += 1
                if char == '"':
                    parse_line += char
                    while char_index < char_count:
                        char = line[char_index]
                        char_index += 1
                        parse_line += char
                        if char == '"':
                            break
                if char in self.WHITESPACE:
                    continue
                if char in self.COMMENT:
                    break
                parse_line += char
            if parse_line:
                parse_lines.append(parse_line)
        line_index = 0
        lines_count = len(parse_lines)
        self.sections = {}
        self.values = {}
        self.values_relative = {}
        while line_index < lines_count:
            line = parse_lines[line_index]
            if line[0] == '[':
                split_char = ']'
                if ':' in line:
                    split_char += ':'
                    section_name, section_parent = line.split(split_char)
                    section_name = section_name[1 : ]    # cut "["
                else:
                    section_name = line.split(split_char)[0][1 : ]
                    section_parent = None
                section = self.LtxSection(section_name, section_parent)
                self.sections[section_name] = section
                start_new_section = False
                line_index += 1
                while not start_new_section and line_index < lines_count:
                    line = parse_lines[line_index]
                    if line[0] == '[':
                        start_new_section = True
                    else:
                        if '=' in line:
                            param_name, param_value = line.split('=')
                            if param_value.startswith('"') and param_value.endswith('"'):
                                param_value = param_value[1 : -2]    # cut " chars
                        else:
                            param_name = line
                            param_value = None
                        section.params[param_name] = param_value
                        line_index += 1
            elif line.startswith('$'):    # fs.ltx
                section = self.LtxSection('root', None)
                self.sections['root'] = section
                value, line = line.split('=')
                line_parts = line
                if '|' in line:
                    line_parts = line.split('|')
                if line_parts[2] == '$fs_root$':
                    self.values[value] = os.path.dirname(self.path)
                    self.values_relative[value] = ''
                elif line_parts[2].startswith('$') and line_parts[2].endswith('$'):
                    if len(line_parts) > 3:
                        self.values[value] = os.path.join(self.values[line_parts[2]], line_parts[3])
                        self.values_relative[value] = os.path.join(self.values_relative[line_parts[2]], line_parts[3])
                    else:
                        self.values[value] = self.values[line_parts[2]]
                        self.values_relative[value] = self.values_relative[line_parts[2]]
                else:
                    self.values[value] = os.path.join(self.values['$sdk_root$'], line_parts[2])
                    self.values_relative[value] = os.path.join(self.values_relative['$sdk_root$'], line_parts[2])
                line_index += 1
            elif line.startswith('#include'):
                line_index += 1
            else:
                raise BaseException('Invalid *.ltx syntax')
