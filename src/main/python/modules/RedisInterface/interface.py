from functools import reduce
from os.path import basename
from tkinter import messagebox
from modules.RedisInterface.Cypher import get_vertex_limited, get_edge_limited, graph_to_cypher, \
    annotation_dict_to_cypher, get_vertex_equal, get_vertex, get_edge, delete_vertex

import redis

from igraph import Graph, plot

from modules.RedisInterface.Exceptions import FileInterfaceFileTypeException, FileInterfaceEmptyFileException
from modules.old.Tags import MERGE_SEPARATOR, SOURCE, TARGET, ID, DATA_SEPARATOR, DISPLAY_SEPARATOR
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

            response = self.__Client.execute_command('GRAPH.QUERY', dbkey, command)

            if report:

                show_report()

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

    def db_merge(self, selection, sourcegraph, targetgraph, targetin=False):

        ### COLLECT ALL OBJECTS ###
        merge_attribute = selection[0]

        if targetin:
            selection.remove(merge_attribute)

        decode = lambda ids: [ID.decode('UTF-8') for ID in ids]

        iid_sets = self.__unify_sets([set(decode(entry)) for entry in self.__query(get_vertex_equal(*selection), sourcegraph)[1:]])
        iid_buckets = {}
        iid_joint = list(reduce(lambda ls, js: ls.union(js), iid_sets))

        index = 0
        for iid_set in iid_sets:

            iid_bucket = {'vertex': [], 'edge': {}, 'id': (merge_attribute + str(index))}
            index += 1

            for iid in iid_set:

                iid_buckets[iid] = iid_bucket

        vertices = self.__response_to_dict(self.__query(get_vertex(*iid_joint), sourcegraph))['v']

        edges = self.__response_to_dict(self.__query(get_edge(*iid_joint), sourcegraph))['edge']

        graph = {'vertices': [], 'edges': []}
        
        for vertex in vertices:

            iid = vertex['id']
            iid_buckets[iid]['vertex'].append(vertex)
            
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

        if sourcegraph == targetgraph:
            self.__query(delete_vertex(*iid_joint), sourcegraph)
            self.db_write(graph, sourcegraph)
        else:
            self.db_write(graph, targetgraph)

    def db_query(self, query, dbkey, to_graph=False):

        if to_graph:

            return self.__response_to_graph(self.__query(query, dbkey))

        else:

            self.__query(query, dbkey)

    def db_explain(self, query, dbkey):

        return self.__Client.execute_command('GRAPH.EXPLAIN', dbkey, query)

    def db_write(self, graph, dbkey):

        self.__query(graph_to_cypher(graph), dbkey, report=True)

        map(lambda target: self.__Client.execute_command('GRAPH.QUERY', dbkey, 'CREATE INDEX ON ' + target),
            [':vertex(id)', ':edge(target)', 'edge(source)'])

    def db_annotate(self, target_property, map_property, property_prefix, dictionaries, dbkey):

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
    def __response_to_dict(response):
        # All entities queried
        entities = list(set(entity.decode('UTF-8').split('.')[0] for entity in response[0]))
        # Init mapping to return
        entity_mapping = {entity: [] for entity in entities}
        # All keys of response objects
        keys = [key.decode('utf-8') for key in response[0]]

        for entry in response[1:]:

            entry_mapping = {keys[index]: entry[index].decode('utf-8') for index in range(len(keys))}

            for entity in entities:

                new_entity_object = {key.split('.')[1]: entry_mapping[key] for key in entry_mapping
                                     if entity == key.split('.')[0]}

                #TODO: USE SET INSTEAD OF CHECK!
                if new_entity_object not in entity_mapping[entity]:
                    entity_mapping[entity].append(new_entity_object)

        return entity_mapping

    def __response_to_graph(self, response):

        def compress_entry(entry_):

            new_entry = {}

            for key in entry_.keys():

                new_key = '_'.join([key.lstrip('e_').lstrip('v_') for key in key.split(DATA_SEPARATOR)])
                new_value = set(entry_[key].split(MERGE_SEPARATOR))
                new_value.discard('NULL')
                new_value = DISPLAY_SEPARATOR.join(new_value)

                new_entry[new_key] = new_value

            return new_entry

        def drop_null_keys(keys, sequence):

            for key in keys:

                if all([entry.attributes()[key] == '' for entry in sequence]):
                    del sequence[key]

        graph = Graph()
        vertices = []
        edges = []
        mapping = self.__response_to_dict(response)

        for entity in mapping:

            for entry in mapping[entity]:

                entry = compress_entry(entry)

                if ID in entry:
                    vertices.append(entry)

                if SOURCE in entry and TARGET in entry:
                    edges.append(entry)

        vertex_identifier = set()
        for vertex in vertices:

            iid = vertex[ID]

            if iid not in vertex_identifier:

                graph.add_vertex(name=iid, **vertex)

                vertex_identifier.add(iid)

        edge_identifier = set()
        for edge in edges:

            source = edge.pop(SOURCE)
            target = edge.pop(TARGET)

            iid = source + target

            if iid not in edge_identifier:

                edge['src'] = source
                edge['tgt'] = target

                graph.add_edge(source=source, target=target, **edge)

                edge_identifier.add(iid)

        for keys_, sequence_ in [(graph.vertex_attributes(), graph.vs), (graph.edge_attributes(), graph.es)]:

            drop_null_keys(keys_, sequence_)

        return graph


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