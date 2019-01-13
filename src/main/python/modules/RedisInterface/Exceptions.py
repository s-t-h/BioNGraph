class FileInterfaceFileTypeException(Exception):

    def __init__(self, file_type):

        super().__init__('A parser for file type ' + file_type + ' is not supported.')


class FileInterfaceParserException(Exception):

    def __init__(self, parser_name, parser_mode):

        super().__init__('The operation ' + parser_mode + ' is not supported for ' + parser_name + ' parser.')


class FileInterfaceEmptyFileException(Exception):

    def __init__(self):

        super().__init__('No file given.')
