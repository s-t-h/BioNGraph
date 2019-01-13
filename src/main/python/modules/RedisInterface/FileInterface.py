from os.path import basename
from modules.GUI.container.File import File
from igraph import plot

from modules.RedisInterface.Exceptions import FileInterfaceFileTypeException, FileInterfaceEmptyFileException


class FileInterface:

    def __init__(self):

        self.__Parser = {}

    def add_parser(self, key, parser):

        self.__Parser[key] = parser

    def read_header(self, path, container, mode):

        file_type, file_name = self.__file_info(path)

        if file_type not in self.__Parser:

            raise FileInterfaceFileTypeException(file_type)

        file = open(path)

        self.__Parser[file_type].set_filename(file_name)
        self.__Parser[file_type].set_mode(mode)
        self.__Parser[file_type].parse(file)

        file.close()

        container[file_name] = File(name=file_name,
                                    path=path,
                                    values=self.__Parser[file_type].get_response(),
                                    ftype=file_type)

    def read_file(self, instruction, file, mode):

        if not file:

            raise FileInterfaceEmptyFileException()

        file_type = file[0]
        file_name = file[1]
        file_path = file[2]

        if file_type not in self.__Parser:

            raise FileInterfaceFileTypeException(file_type)

        file = open(file_path)

        try:

            self.__Parser[file_type].set_mode(mode)
            self.__Parser[file_type].set_filename(file_name)
            self.__Parser[file_type].set_instruction(instruction)
            self.__Parser[file_type].parse(file)

            return self.__Parser[file_type].get_response()

        finally:

            file.close()

    def write_file(self, path, graph):

        file_type, file_name = self.__file_info(path)

        if file_type not in ['graphml', 'png']:

            raise FileInterfaceFileTypeException(file_type)

        if file_type == 'graphml':

            try:

                file = open(path)

            except FileNotFoundError:

                file = open(path, 'w+')

            try:

                graph.write_graphml(f=file)

            finally:

                file.close()

        elif file_type == 'png':

            def set_visual_style():

                vertex_color_map = {}
                edge_color_map = {}

                for property_count, color_map in [(len(graph.vertex_attributes()), vertex_color_map),
                                                  (len(graph.edge_attributes()), edge_color_map)]:

                    rgb_fraction = round(255 / max(1, property_count))

                    for count in range(property_count + 1):
                        color_map[count] = ', '.join([str(min(255, 0 + rgb_fraction * count)),
                                                      str(200),
                                                      str(max(0, 255 - rgb_fraction * count))])

                visual_style = {
                    'vertex_color': [
                        vertex_color_map[len([attribute for attribute in vertex.attributes().values() if attribute])]
                        for
                        vertex in graph.vs],
                    'edge_color': [
                        edge_color_map[len([attribute for attribute in edge.attributes().values() if attribute])]
                        for edge in graph.es]
                }

                return visual_style

            plot(graph, path, **set_visual_style())

    @staticmethod
    def __file_info(path):

        return basename(path).split('.')[1], basename(path).split('.')[0]
