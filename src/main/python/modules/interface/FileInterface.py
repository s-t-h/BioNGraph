from os.path import basename
from modules.container.File import File


class FileInterface:

    def __init__(self):

        self.__Parser = {}
        self.Files = {}

    def add_parser(self, key, parser):

        self.__Parser[key] = parser

    def read_header(self, path, container):

        file_type, file_name = self.__file_info(path)

        if file_type in self.__Parser:

            file = open(path)

            self.__Parser[file_type].set_filename(file_name)
            self.__Parser[file_type].set_mode('header')
            self.__Parser[file_type].parse(file)

            file.close()

            container[file_name] = File(name=file_name,
                                        path=path,
                                        values=self.__Parser[file_type].get_response(),
                                        ftype=file_type)

        else:
            raise Exception('No reader for file type found.')

    def read_file(self, instruction=None, file=None, path=None):

        if file:
            file_type = file.Type
            file_name = file.Name
            file_path = file.Path

        elif path:
            file_type, file_name = self.__file_info(path)
            file_path = path

        else:
            raise Exception('No file given.')

        if file_type in self.__Parser:
            file = open(file_path)

            self.__Parser[file_type].set_mode('file')
            self.__Parser[file_type].set_filename(file_name)
            self.__Parser[file_type].set_instruction(instruction)
            self.__Parser[file_type].parse(file)

            file.close()

            return self.__Parser[file_type].get_response()

    def write_file(self, path, query):

        file_type, file_name = self.__file_info(path)

        if file_type == 'graphml':

            try:
                file = open(path)

            except FileNotFoundError:
                file = open(path, 'w+')

            query.save_as_graphml(file)

            file.close()

        elif file_type == 'png':

            query.save_as_png(path)

        else:
            raise Exception('No writer for the choosen file type found.')

    @staticmethod
    def __file_info(path):

        return basename(path).split('.')[1], basename(path).split('.')[0]
