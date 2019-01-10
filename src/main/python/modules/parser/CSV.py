import csv

from modules.container.Graph import Graph
from modules.container.Tags import DATA_SEPARATOR, TARGET, SOURCE, ID


class CSVParser:

    def __init__(self):
        self.__Response = None

        self.__Mode = None
        self.__Filename = None
        self.__Instruction = None

    def set_mode(self, mode):

        self.__Mode = mode

    def set_filename(self, filename):

        self.__Filename = filename

    def set_instruction(self, instruction):

        self.__Instruction = instruction

    def get_response(self):

        return self.__Response

    def parse(self, file):

        if self.__Mode == 'header':

            def collect_vertex_attributes(attributes, container):

                add_attribute = lambda: container.add(attributes.pop(0).split('_')[1])

                while 'id' not in attributes[0]:
                    add_attribute()
                attributes.pop(0)

                return container

            self.__Response = []

            csv_reader = csv.reader(file)
            header = next(csv_reader)

            source_attributes = collect_vertex_attributes(header, set())
            target_attributes = collect_vertex_attributes(header, set())
            edge_attributes = header

            self.__Response = \
                list(source_attributes.union(target_attributes)) + edge_attributes

        elif self.__Mode == 'file':

            def collect_vertex(items):

                vertex = {}

                while 'id' not in items[0][0]:

                    matching_key = check_key(items[0][0])

                    if matching_key:
                        vertex[matching_key] = items.pop(0)[1].replace(',', ';')
                    else:
                        items.pop(0)

                vertex['id'] = self.__Filename + DATA_SEPARATOR + items.pop(0)[1]

                return vertex

            def collect_edge(items):

                edge = {}

                while items:

                    matching_key = check_key(items[0][0])

                    if matching_key:
                        edge[matching_key] = items.pop(0)[1].replace(',', ';')

                    else:
                        items.pop(0)

                return edge

            def check_key(key):

                for attribute in self.__Instruction:

                    if attribute in key:
                        return self.__Filename + DATA_SEPARATOR + attribute

                return False

            self.__Response = {'vertices': [], 'edges': []}

            csv_reader = csv.DictReader(file)

            for entry in csv_reader:

                entry = list(entry.items())

                try:
                    source = collect_vertex(entry)
                    target = collect_vertex(entry)
                    edge = collect_edge(entry)
                except TypeError:
                    continue

                edge[TARGET] = target[ID]
                edge[SOURCE] = source[ID]

                self.__Response['vertices'].append(source)
                self.__Response['vertices'].append(target)
                self.__Response['edges'].append(edge)

            print(self.__Response)