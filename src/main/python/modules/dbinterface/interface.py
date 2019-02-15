from itertools import chain
from os.path import basename, abspath, join, dirname
from os import remove
from subprocess import Popen, PIPE, check_call
from tkinter import messagebox
from csv import DictWriter
from modules.RedisInterface.Cypher import get_vertex_limited, get_edge_limited, graph_to_cypher, \
    annotation_dict_to_cypher, get_merge_entities, get_merge_values
from modules.RedisInterface.constants import WORK_DIRECTORY, REDIS_BULK_DIRECTORY, PYTHON_EXEC
from time import time

import redis

from igraph import Graph, plot

from modules.RedisInterface.Exceptions import FileInterfaceFileTypeException, FileInterfaceEmptyFileException
from modules.old.Tags import MERGE_SEPARATOR, SOURCE, TARGET, ID, DATA_SEPARATOR, DISPLAY_SEPARATOR, VERTEX, EDGE
from modules.gui.container import OpenFile


class DataBaseInterface:

    def __init__(self, file_interface):
        self.__Client = None
        self.__FileInterface = file_interface

        self.__host = None
        self.__port = None

    # Client methods
    def client_connect(self, host, port):

        self.__Client = redis.StrictRedis(host=host, port=port)
        self.__host = host
        self.__port = port

    def client_disconnect(self):

        self.__Client.execute_command('QUIT')

        self.__Client = None

    def client_get_connection(self):

        try:
            return self.__Client.ping()

        except redis.ConnectionError:
            return False

        except ConnectionRefusedError:
            return False

        except AttributeError:
            return False

    def client_shutdown(self):

        self.__Client.execute_command('SHUTDOWN SAVE')

    def __query(self, command, dbkey, report=False):

        if self.client_get_connection():

            response = self.__Client.execute_command('GRAPH.QUERY', dbkey, command)

            if report:
                self.__show_report(response[1])

            return response[0]

    # DB methods
    def db_save(self):

        self.__Client.execute_command('SAVE')

    def db_get_keys(self):

        try:

            return [graph.decode('UTF-8') for graph in self.__Client.execute_command('KEYS *')]

        except redis.ResponseError:

            return []

    def db_get_attributes(self):

        try:

            vertex_attributes = []
            edge_attribute = []

            for key in self.db_get_keys():

                try:
                    vertex_attributes.extend([attribute.decode('utf-8').split('.')[1] for attribute
                                              in self.__query(get_vertex_limited(), key)[0]])

                    edge_attribute.extend([attribute.decode('utf-8').split('.')[1] for attribute
                                           in self.__query(get_edge_limited(), key)[0]])

                except IndexError:
                    pass

            return \
                (vertex_attributes,
                 edge_attribute)

        except TypeError:

            return [], []

        except redis.ResponseError:

            return [], []

    def db_delete_key(self, dbkey):

        self.__Client.execute_command('GRAPH.DELETE ' + dbkey)

    def db_merge(self, selection, source_graphs, target_graph):

        def extract_(entity, *args):

            merge_property_values = set()

            for key in args:

                try:
                    merge_property_values.add(entity[key])

                except KeyError:
                    pass

            merge_property_values.discard('NULL')

            return merge_property_values.pop()

        merge_property_name = target_graph + DATA_SEPARATOR + selection.pop(0)

        start = time()

        distinct_values = set()
        for source_graph in source_graphs:
            values = set(value.decode('UTF-8') for value in
                         chain.from_iterable(self.__query(get_merge_values(*selection), source_graph)[1:]))
            distinct_values.update(values)
        distinct_values.discard('NULL')

        end = time()
        print('Get distinct values: ' + str(end - start))
        print()

        start = time()

        response = ([],[])
        vertex_properties = set()
        edge_properties = set()

        for source_graph in source_graphs:

            vertices, edges = \
                self.__split_mapping(
                    self.__response_to_dict(
                        self.__query(get_merge_entities(), source_graph),
                        decode=True
                    )
                )

            print('Vertices: ' + str(len(vertices)))
            print('Edges: ' + str(len(edges)))

            vertex_properties.update(list(vertices[0].keys()))
            edge_properties.update(list(edges[0].keys()))

            response[0].extend(vertices)
            response[1].extend(edges)

        end = time()
        print('Query for entities to merge: ' + str(end - start))
        print()

        buckets = {}
        start = time()
        index = 0
        for value in distinct_values:
            buckets[value] = {'vertex': [], 'edge': {}, 'id': (merge_property_name + str(index))}
            index += 1

        end = time()
        print('Initialize buckets: ' + str(end - start))
        print()

        start = time()
        for vertex in response[0]:
            bucket = buckets[extract_(vertex, *selection)]
            bucket['vertex'].append(vertex)
            buckets[vertex['id']] = bucket
        end = time()
        print('Sort vertices in buckets: ' + str(end - start))
        print()

        start = time()
        for edge in response[1]:
            edge_source = edge[SOURCE]
            edge_target = edge[TARGET]
            edge[SOURCE] = buckets[edge_source]['id']
            edge[TARGET] = buckets[edge_target]['id']
            edge_id = edge[SOURCE] + edge[TARGET]

            bucket = buckets[edge_source]

            if edge_id in bucket['edge']:

                bucket['edge'][edge_id].append(edge)

            else:

                bucket['edge'][edge_id] = [edge]
        end = time()
        print('Sort edges in buckets: ' + str(end - start))
        print()

        start = time()
        graph = {'vertices': [], 'edges': []}
        merged = 0
        for value in distinct_values:

            bucket = buckets[value]

            if bucket['vertex']:

                if len(bucket['vertex']) > 1:
                    merged += 1

                merged_vertex = self.__merge_dictionaries(bucket['vertex'], vertex_properties)
                merged_vertex['id'] = bucket['id']
                merged_vertex[merge_property_name] = value

                for property_ in selection:
                    merged_vertex[property_] = 'NULL'

                graph['vertices'].append(merged_vertex)

                for edge_id in bucket['edge']:
                    merged_edge = self.__merge_dictionaries(bucket['edge'][edge_id], edge_properties)
                    merged_edge[TARGET] = set(merged_edge[TARGET].split(MERGE_SEPARATOR)).pop()
                    merged_edge[SOURCE] = set(merged_edge[SOURCE].split(MERGE_SEPARATOR)).pop()

                    graph['edges'].append(merged_edge)
        end = time()
        print('Merge entities: ' + str(end - start))
        print('Total merged: ' + str(merged))
        print()

        self.db_write(graph, target_graph)

    def db_query(self, query, dbkey, to_graph=False):

        if to_graph:

            return \
                self.__split_mapping(
                    self.__response_to_dict(
                        self.__revise_response(
                            self.__query(query, dbkey)
                        ),
                        decode=False
                    )
                )

        else:

            self.__query(query, dbkey)

    def db_explain(self, query, dbkey):

        return self.__Client.execute_command('GRAPH.EXPLAIN', dbkey, query)

    def db_write(self, graph, graph_key):

        start = time()
        self.__FileInterface.write_bulk(graph, graph_key)
        end = time()
        print('Write csv files: ' + str(end - start))

        start = time()

        exec_redis_bulk = PYTHON_EXEC + join(abspath(dirname(__file__)), REDIS_BULK_DIRECTORY)
        nodes = join(abspath(dirname(__file__)), WORK_DIRECTORY) + graph_key + '_nodes.csv'
        edges = join(abspath(dirname(__file__)), WORK_DIRECTORY) + graph_key + '_edges.csv'

        command = \
            ' '.join([exec_redis_bulk, graph_key]) + \
            ' -h ' + self.__host + ' -p ' + self.__port + \
            ' -n ' + nodes + ' -r ' + edges

        try:
            process = Popen(command, stdin=PIPE, stdout=PIPE, shell=True)
            process.wait()
            response = process.stdout.read()
            print(response)

        finally:

            try:
                remove(nodes)
                remove(edges)

            except FileNotFoundError:
                pass

        end = time()
        print('Upload stuff: ' + str(end - start))

    def db_annotate(self, target_property, map_property, property_prefix, dictionaries, dbkey):

        distinct_values = set(value.decode('UTF-8') for value in
                              chain.from_iterable(self.__query(get_merge_values(target_property), dbkey)[1:]))
        distinct_values.discard('NULL')

        dictionaries = [dictionary for dictionary in dictionaries if dictionary[map_property] in distinct_values]

        self.__query(annotation_dict_to_cypher(target_property, map_property, property_prefix, dictionaries),
                     dbkey, report=True)

    @staticmethod
    def __unify_sets(sets):

        unions = []

        while sets:

            union = sets.pop(0)
            changed = True

            while changed:

                changed = False

                for remaining in sets:

                    if union.intersection(remaining):
                        union = union.union(remaining)
                        sets.remove(remaining)

                        changed = True

            unions.append(union)

        return unions

    @staticmethod
    def __merge_dictionaries(dictionaries, keys):

        merged_dictionary = {}

        for key in keys:

            values = []

            for dictionary in dictionaries:

                try:
                    values.append(dictionary[key])

                except KeyError:
                    pass

            merged_dictionary[key] = MERGE_SEPARATOR.join(values)

        return merged_dictionary

    @staticmethod
    def __response_to_dict(response, decode=True):

        def get_binder_intervals():

            start = 0

            end = 0

            intervals = []

            symbol = binder[0]

            for index in range(1, len(binder) + 1):

                if index > len(binder) - 1:
                    intervals.append(range(start, end + 1))

                    break

                next_symbol = binder[index]

                if next_symbol != symbol:

                    end += 1

                    intervals.append(range(start, end))

                    symbol = next_symbol

                    start = end

                else:

                    end += 1

            return intervals

        def decode_(value):

            if decode:

                return value.decode('UTF-8')

            else:

                return value

        binder, keys = zip(*[decode_(value).split('.') for value in response[0]])
        binder_intervals = get_binder_intervals()

        mapping = \
            [
                {keys[index]: decode_(entry[index]) for index in interval}
                for interval in binder_intervals
                for entry in response[1:]
            ]

        return mapping

    @staticmethod
    def __revise_response(response):

        def revise_keys():

            response[0] = ['_'.join([key.replace('e_', '').replace('v_', '')
                                     for key in key.decode('UTF-8').split(DATA_SEPARATOR)])
                           for key in response[0]]

        def revise_values():

            for index in range(1, len(response)):
                response[index] = [DISPLAY_SEPARATOR.join([value
                                                           for value in
                                                           set(value.decode('UTF-8').split(MERGE_SEPARATOR))
                                                           if value != 'NULL'])
                                   for value in response[index]]

        def drop_null_keys():

            columns = list(zip(*response))

            dropped = 0

            for index in range(len(response[0])):

                if all([value == '' for value in columns[index][1:]]):

                    for entry in response:
                        entry.pop(index - dropped)

                    dropped += 1

        revise_keys()
        revise_values()
        drop_null_keys()

        return response

    @staticmethod
    def __split_mapping(mapping):

        return (list({v[ID]: v for v in mapping if ID in v}.values()),
                list({e[SOURCE] + e[TARGET]: e for e in mapping if SOURCE in e and TARGET in e}.values()))

    @staticmethod
    def __show_report(response):

        messagebox.showinfo(title='RedisGraph',
                            message='Executed database query: \n' +
                                    '\n'.join([str(content) for content in response]))


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

        container[file_name] = OpenFile(name=file_name,
                                        path=path,
                                        values=self.__Parser[file_type].get_response(),
                                        file_type=file_type)

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

    def write_file(self, path, query):

        file_type, file_name = self.__file_info(path)

        if file_type not in ['graphml', 'png']:
            raise FileInterfaceFileTypeException(file_type)

        if file_type == 'graphml':

            self.__write_graphml(self.__create_igraph(query[0], query[1]), path)

        elif file_type == 'png':

            self.__write_png(self.__create_igraph(query[0], query[1]), path)

    @staticmethod
    def write_bulk(graph, graph_key):

        vertex_properties = [key for key in graph['vertices'][0].keys() if key != 'id']
        edge_properties = list(graph['edges'][0].keys())

        path_ = join(abspath(dirname(__file__)), WORK_DIRECTORY)

        with open(path_ + graph_key + '_nodes.csv', 'w', newline='') as nodes:
            fieldnames = ['id'] + vertex_properties
            writer = DictWriter(nodes, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(graph['vertices'])

        with open(path_ + graph_key + '_edges.csv', 'w', newline='') as edges:
            fieldnames = ['source', 'target'] + edge_properties
            writer = DictWriter(edges, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(graph['edges'])

    @staticmethod
    def __write_graphml(graph, path):

        try:

            file = open(path)

        except FileNotFoundError:

            file = open(path, 'w+')

        try:

            graph.write_graphml(f=file)

        finally:

            file.close()

    @staticmethod
    def __write_png(graph, path):

        def set_visual_style():

            vertex_color_map = {}
            edge_color_map = {}

            for property_count, color_map in [(len(graph.vertex_attributes()), vertex_color_map),
                                              (len(graph.edge_attributes()), edge_color_map)]:

                rgb_fraction = round(255 / max(1, property_count))

                for count in range(property_count + 1):
                    color_map[count] = ', '.join([str(min(255, 0 + rgb_fraction * count)),
                                                  str(94),
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

        plot(graph, path, bbox=(2000, 2000), **set_visual_style())

    @staticmethod
    def __create_igraph(vertices, edges):

        graph = Graph()

        for v in vertices:
            graph.add_vertex(name=v.pop(ID), **v)

        for e in edges:
            graph.add_edge(source=e.pop(SOURCE), target=e.pop(TARGET), **e)

        return graph

    @staticmethod
    def __file_info(path):

        return str(basename(path).split('.')[1]), str(basename(path).split('.')[0])
