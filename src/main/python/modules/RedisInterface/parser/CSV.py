import csv

from modules.RedisInterface.parser.Parser import Parser
from modules.container.Tags import DATA_SEPARATOR, TARGET, SOURCE, ID


class CSVParser(Parser):

    def __init__(self):

        super().__init__()

    def parse(self, file):

        if self._Mode == 'header':

            def collect_vertex_attributes(attributes, container):

                add_attribute = lambda: container.add(attributes.pop(0).split('_')[1])

                while 'id' not in attributes[0]:
                    add_attribute()
                attributes.pop(0)

                return container

            self._Response = []

            csv_reader = csv.reader(file)
            header = next(csv_reader)

            source_attributes = collect_vertex_attributes(header, set())
            target_attributes = collect_vertex_attributes(header, set())
            edge_attributes = header

            self._Response = \
                list(source_attributes.union(target_attributes)) + edge_attributes

        elif self._Mode == 'file':

            def collect_vertex(items):

                vertex = {}

                while 'id' not in items[0][0]:

                    matching_key = check_key(items[0][0])

                    if matching_key:
                        vertex[matching_key] = items.pop(0)[1].replace(',', ';')
                    else:
                        items.pop(0)

                vertex['id'] = self._Filename + DATA_SEPARATOR + items.pop(0)[1]

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

                for attribute in self._Instruction:

                    if attribute in key:
                        return self._Filename + DATA_SEPARATOR + attribute

                return False

            self._Response = {'vertices': [], 'edges': []}
            identifiers = set()
            csv_reader = csv.DictReader(file)


            for entry in csv_reader:

                entry = list(entry.items())

                try:

                    source = collect_vertex(entry)
                    target = collect_vertex(entry)
                    edge = collect_edge(entry)

                except TypeError:

                    continue

                edge[SOURCE] = source[ID]
                edge[TARGET] = target[ID]

                if source[ID] not in identifiers:

                    self._Response['vertices'].append(source)
                    identifiers.add(source[ID])

                if target[ID] not in identifiers:

                    self._Response['vertices'].append(target)
                    identifiers.add(target[ID])

                if edge[SOURCE] + edge[TARGET] not in identifiers:

                    self._Response['edges'].append(edge)
                    identifiers.add(edge[SOURCE] + edge[TARGET])