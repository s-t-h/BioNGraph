from functools import reduce
from modules.constructor.Cypher import get_vertex_limited, get_edge_limited, graph_to_cypher, \
    annotation_dict_to_cypher, get_vertex_equal, get_vertex, get_edge, delete_vertex

import redis

from modules.container.Graph import Graph
from modules.container.Tags import MERGE_SEPARATOR, SOURCE, TARGET, ID


class DatabaseInterface:

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

    def __query(self, command, dbkey, post=False):

        if self.client_get_connection():

            response = self.__Client.execute_command('GRAPH.QUERY', dbkey, command)

            '''
            if self.Log and post:
                self.Log.config(state=NORMAL)
                self.Log.insert(END, '> ' + str(response[1]) + '\n')
                self.Log.config(state=DISABLED)
            '''

            return response[0]

    # DB methods
    def db_save(self):

        self.__Client.execute_command('SAVE')

    def db_get_keys(self):

        return [graph.decode('UTF-8') for graph in self.__Client.execute_command('KEYS *')]

    def db_get_attributes(self, dbkey):

        try:
            vertexattr = self.__query(get_vertex_limited(), dbkey)
            edgeattr = self.__query(get_edge_limited(), dbkey)

            return \
                ([attribute.decode('utf-8').split('.')[1] for attribute
                 in vertexattr[0]
                 if attribute.decode('utf-8').split('.')[1] != 'id'],
                [attribute.decode('utf-8').split('.')[1] for attribute
                 in edgeattr[0]
                 if attribute.decode('utf-8').split('.')[1] != 'id'
                 and attribute.decode('utf-8').split('.')[1] != 'target'
                 and attribute.decode('utf-8').split('.')[1] != 'source'])

        except TypeError:
            return [], []

        except redis.ResponseError:
            return [],[]

    def db_delete_key(self, dbkey):

        self.__Client.execute_command('GRAPH.DELETE ' + dbkey)

    def db_merge(self, selection, sourcegraph, targetgraph, targetin=False):
        self.__Client.execute_command('GRAPH.QUERY', sourcegraph, 'CREATE INDEX ON :vertex(id)')
        self.__Client.execute_command('GRAPH.QUERY', sourcegraph, 'CREATE INDEX ON :edge(target)')
        self.__Client.execute_command('GRAPH.QUERY', sourcegraph, 'CREATE INDEX ON :edge(source)')

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

    def db_query(self, query, dbkey):

        return (self.__response_to_graph(self.__query(query, dbkey)))

    def db_write(self, graph, dbkey):

        self.__query(graph_to_cypher(graph), dbkey, post=True)

    def db_annotate(self, dictionary, dbkey):

        self.__query(annotation_dict_to_cypher(dictionary), dbkey, post=True)

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

        graph = Graph()
        vertex_keys = set()
        edge_keys = set()

        mapping = self.__response_to_dict(response)

        for entity in mapping:

            for entry in mapping[entity]:

                if ID in entry:
                    graph.add_vertex(entry)
                    vertex_keys = vertex_keys.union(entry.keys())

                if SOURCE in entry and TARGET in entry:
                    graph.add_edge(entry)
                    edge_keys = edge_keys.union(entry.keys())

        def drop_null_keys(keys, objects):
            null_keys = []
            for key in keys:
                null_key = all(map(lambda obj: bool(obj[key] == 'NULL'), objects))
                if null_key:
                    null_keys.append(key)
                    for obj in objects:
                        del obj[key]
            for key in null_keys:
                keys.discard(key)

        for keys, objects in [(vertex_keys, graph.Vertices), (edge_keys, graph.Edges)]:
            drop_null_keys(keys, objects)

        return list(vertex_keys), list(edge_keys), graph

