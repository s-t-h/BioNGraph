from os.path import basename
from modules.container.File import File
from igraph import plot


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

    def write_file(self, path, graph):

        file_type, file_name = self.__file_info(path)

        try:

            file = open(path)

        except FileNotFoundError:

            file = open(path, 'w+')

        if file_type == 'graphml':

            graph.write_graphml(f=file)

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
                        for vertex in graph.vs],
                    'edge_color': [
                        edge_color_map[len([attribute for attribute in edge.attributes().values() if attribute])] for
                        edge in graph.es]
                }

                return visual_style

            plot(graph, file, **set_visual_style())

            graph.save_as_png(path)

            file.close()

        else:

            file.close()

            raise Exception('No writer for the choosen file type found.')

    @staticmethod
    def __file_info(path):

        return basename(path).split('.')[1], basename(path).split('.')[0]
