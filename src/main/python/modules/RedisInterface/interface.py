from functools import reduce
from itertools import chain
from os.path import basename
from tkinter import messagebox
from time import time
from modules.RedisInterface.Cypher import get_vertex_limited, get_edge_limited, graph_to_cypher, \
    annotation_dict_to_cypher, get_merge_entities, get_merge_values
from time import time

import redis

from igraph import Graph, plot

from modules.RedisInterface.Exceptions import FileInterfaceFileTypeException, FileInterfaceEmptyFileException
from modules.old.Tags import MERGE_SEPARATOR, SOURCE, TARGET, ID, DATA_SEPARATOR, DISPLAY_SEPARATOR, VERTEX, EDGE
from modules.gui.container import OpenFile


class DataBaseInterface:

    def __init__(self):
        self.__Client = None

    # Client methods
    def client_connect(self, host, port):

        self.__Client = redis.StrictRedis(host=host, port=port)

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

        def show_report():

            messagebox.showinfo(title='Redis',
                                message='Executed database query: \n' +
                                        '\n'.join([content.decode('UTF-8') for content in response[1]])
                                )

        if self.client_get_connection():

            start = time()
            response = self.__Client.execute_command('GRAPH.QUERY', dbkey, command)

            if report:

                show_report()
                end = time()
                print('Query database: ' + str(end - start))

            return response[0]

    # DB methods
    def db_save(self):

        self.__Client.execute_command('SAVE')

    def db_get_keys(self):

        try:

            return [graph.decode('UTF-8') for graph in self.__Client.execute_command('KEYS *')]

        except redis.ResponseError:

            return []

    def db_get_attributes(self, dbkey):

        try:

            return \
                ([attribute.decode('utf-8').split('.')[1] for attribute
                 in self.__query(get_vertex_limited(), dbkey)[0]],
                [attribute.decode('utf-8').split('.')[1] for attribute
                 in self.__query(get_edge_limited(), dbkey)[0]])

        except TypeError:

            return [], []

        except redis.ResponseError:

            return [],[]

    def db_delete_key(self, dbkey):

        self.__Client.execute_command('GRAPH.DELETE ' + dbkey)

    def db_merge(self, selection, sourcegraph, targetgraph, targetin=True):

        def extract_(entity, *args):

            key_ = set(map(lambda key: entity[key], args))
            key_.discard('NULL')

            return key_.pop()

        merge_property = selection[0]
        selection.remove(merge_property)

        start = time()
        distinct_values = set(value.decode('UTF-8') for value in
                              chain.from_iterable(self.__query(get_merge_values(*selection), sourcegraph)[1:]))
        distinct_values.discard('NULL')
        end = time()
        print('Get distinct values: ' + str(end - start))
        print()

        start = time()
        response = \
            self.__split_mapping(
                    self.__response_to_dict(
                        self.__query(get_merge_entities(*selection), sourcegraph),
                        decode=True
                    )
            )
        end = time()
        print('Query for entities to merge: ' + str(end - start))
        print()

        buckets = {}
        start = time()
        index = 0
        for value in distinct_values:

            buckets[value] = {'vertex': [], 'edge': {}, 'id': (merge_property + str(index))}
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
        for value, bucket in buckets.items():

            if bucket['vertex']:

                merged_vertex = self.__merge_dictionaries(bucket['vertex'])
                merged_vertex['id'] = bucket['id']
                merged_vertex[merge_property] = value

                for property_ in selection:
                    merged_vertex[property_] = 'NULL'

                graph['vertices'].append(merged_vertex)

                for edge_id in bucket['edge']:
                    merged_edge = self.__merge_dictionaries(bucket['edge'][edge_id])
                    merged_edge[TARGET] = set(merged_edge[TARGET].split(MERGE_SEPARATOR)).pop()
                    merged_edge[SOURCE] = set(merged_edge[SOURCE].split(MERGE_SEPARATOR)).pop()

                    graph['edges'].append(merged_edge)
        end = time()
        print('Merge entities: ' + str(end - start))
        print()

        self.db_write(graph, targetgraph, label_=targetgraph, type_=targetgraph)

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

    def db_write(self, graph, dbkey, label_=VERTEX, type_=EDGE):

        start = time()

        graph = graph_to_cypher(graph, label_=label_, type_=type_)
        self.__query(graph, dbkey, report=True)

        end = time()
        print('Write graph into database: ' + str(end - start))

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
    def __merge_dictionaries(dictionaries):

        keys = list(dictionaries[0].keys())

        merged_dictionary = {key: MERGE_SEPARATOR.join([d[key] for d in dictionaries])
                             for key in keys}

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

        start = time()

        binder, keys = zip(*[decode_(value).split('.') for value in response[0]])
        binder_intervals = get_binder_intervals()

        mapping = \
            [
                {keys[index]: decode_(entry[index]) for index in interval}
                for interval in binder_intervals
                for entry in response[1:]
        ]

        end = time()
        print('Mapping response to dict: ' + str(end - start))

        return mapping

    @staticmethod
    def __revise_response(response):

        start = time()

        def revise_keys():

            response[0] = ['_'.join([key.lstrip('e_').lstrip('v_')
                                     for key in key.decode('UTF-8').split(DATA_SEPARATOR)])
                           for key in response[0]]

        def revise_values():

            for index in range(1, len(response)):

                response[index] = [DISPLAY_SEPARATOR.join([value
                                                           for value in set(value.decode('UTF-8').split(MERGE_SEPARATOR))
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

        end = time()
        print('Revise response: ' + str(end-start))

        return response

    @staticmethod
    def __split_mapping(mapping):

        start = time()

        a = (list({v[ID]: v for v in mapping if ID in v}.values()),
                list({e[SOURCE] + e[TARGET]: e for e in mapping if SOURCE in e and TARGET in e}.values()))

        end = time()
        print('Sort mapping: ' + str(end-start))

        return a

    '''
        def db_merge(self, selection, sourcegraph, targetgraph, targetin=True):

        ### COLLECT ALL OBJECTS ###
        merge_attribute = selection[0]

        if not targetin:
            selection.remove(merge_attribute)

        decode = lambda ids: [ID.decode('UTF-8') for ID in ids]

        start = time()
        iid_sets = self.__unify_sets([set(decode(entry)) for entry in self.__query(get_vertex_equal(*selection), sourcegraph)[1:]])
        end = time()
        print('Collect IDs: ' + str(end - start))

        iid_buckets = {}
        iid_joint = list(reduce(lambda ls, js: ls.union(js), iid_sets))

        start = time()
        index = 0
        for iid_set in iid_sets:

            iid_bucket = {'vertex': [], 'edge': {}, 'id': (merge_attribute + str(index))}
            index += 1

            for iid in iid_set:

                iid_buckets[iid] = iid_bucket
        end = time()
        print('Initialize buckets: ' + str(end - start))

        start = time()
        vertex_response = self.__query(get_vertex(*iid_joint), sourcegraph)
        end = time()
        print('Collect vertices: ' + str(end - start))

        vertices = self.__response_to_dict(vertex_response)

        start = time()
        edge_response = self.__query(get_edge(*iid_joint), sourcegraph)
        end = time()
        print('Collect edges: ' + str(end - start))

        edges = self.__response_to_dict(edge_response)

        graph = {'vertices': [], 'edges': []}

        start = time()
        for vertex in vertices:

            iid = vertex['id']
            iid_buckets[iid]['vertex'].append(vertex)
        end = time()
        print('Sort vertices in buckets: ' + str(end - start))

        start = time()
        for edge in edges:

            iid_source = edge[SOURCE]
            iid_target = edge[TARGET]

            if iid_target in iid_buckets and iid_source in iid_buckets:

                edge[SOURCE] = iid_buckets[iid_source]['id']
                edge[TARGET] = iid_buckets[iid_target]['id']

                edge_key = edge[SOURCE] + edge[TARGET]

                if edge_key in iid_buckets[iid_source]['edge']:

                    iid_buckets[iid_source]['edge'][edge_key].append(edge)

                else:

                    iid_buckets[iid_source]['edge'][edge_key] = [edge]

        end = time()
        print('Sort edges in buckets: ' + str(end - start))

        start = time()
        for iid in [iid_set.pop() for iid_set in iid_sets]:

            merged_vertex = self.__merge_dictionaries(iid_buckets[iid]['vertex'])
            merged_vertex['id'] = iid_buckets[iid]['id']

            merge_attribute_value = MERGE_SEPARATOR.join([merged_vertex[attribute] for attribute in selection])
            merge_attribute_value = set(value for value in merge_attribute_value.split(MERGE_SEPARATOR))
            merge_attribute_value.discard('NULL')
            merge_attribute_value = merge_attribute_value.pop()

            for attribute in selection:
                merged_vertex[attribute] = 'NULL'
            merged_vertex[merge_attribute] = merge_attribute_value

            graph['vertices'].append(merged_vertex)

            for edge_key in iid_buckets[iid]['edge']:

                merged_edge = self.__merge_dictionaries(iid_buckets[iid]['edge'][edge_key])

                merged_edge[TARGET] = set(merged_edge[TARGET].split(MERGE_SEPARATOR)).pop()
                merged_edge[SOURCE] = set(merged_edge[SOURCE].split(MERGE_SEPARATOR)).pop()
                graph['edges'].append(merged_edge)
        end = time()
        print('Merge entities: ' + str(end - start))

        if sourcegraph == targetgraph:

            self.__query(delete_vertex(*iid_joint), sourcegraph)
            self.db_write(graph, sourcegraph)

        else:

            self.db_write(graph, targetgraph, label_=targetgraph, type_=targetgraph)

        end = time()
    '''


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