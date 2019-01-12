class FileInterfaceParserException(Exception):

    def __init__(self, file_type):

        Exception.__init__('A parser for file type ' + file_type + ' is not supported.')
