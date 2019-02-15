from itertools import chain
from os.path import basename, abspath, join, dirname
from os import remove
from subprocess import Popen, PIPE
from tkinter import messagebox
from csv import DictWriter
from modules.dbinterface.cypher import get_vertex_limited, get_edge_limited, get_entities, get_values
from modules.dbinterface.constants import WORK_DIRECTORY, REDIS_BULK_DIRECTORY, PYTHON_EXEC, G_EXPLAIN
from igraph import Graph, plot
from modules.dbinterface.exceptons import FileInterfaceFileTypeException, FileInterfaceEmptyFileException
from modules.dbinterface.constants import QUIT, G_QUERY, UTF_8, KEYS, G_DELETE,  MERGE_SEPARATOR, SOURCE, TARGET, ID, \
    DATA_SEPARATOR, DISPLAY_SEPARATOR, VERTEX, EDGE
from modules.gui.container import OpenFile

import redis


class DataBaseInterface:
    """
    Comprises methods to connect and access a Redis instance.

    This class is used by the `DataBaseStatus` class to send query and import requests to
    a Redis instance. Comprises the Property Collision Based Merging algorithm to merge
    graphs.

    Attributes
    ----------
    __Client : StrictRedis
        Redis server client.

    __FileInterface : FileInterface
        Interface used to bulk upload graphs.

    __host : str
        The host used to initialize the Redis client.

    __port : str
        The port used to initialize the Redis client.

    Methods
    -------
    client_connect(host, port)
        Initializes a connection to a database.

    client_disconnect()
        Disconnects from a database.

    client_get_connection()
        Returns the current connection status.

    db_save()
        Saves the database to disk.

    db_get_keys()
        Returns all available graph keys stored.

    db_get_attributes()
        Returns all properties stored in the connected dabase.

    db_delete_key(dbkey)
        Deletes the graph specified by dbkey.

    db_merge(selection, source_graphs, target_graph)
        Calculates the merge graph of a list of source_graphs with respect to a list of properties.

    db_query(query, dbkey, to_graph)
        Queries a specified graph.

    db_explain(query, dbkey)
        Returns the execution plan of a query.

    db_write(graph, graph_key)
        Writes a new graph to the database.
    """

    def __init__(self, file_interface: 'FileInterface'):
        """
        Initializes a new DataBaseInterface instance.

        Initially only the __FileInterface is set.

        Parameters
        ----------
        file_interface : FileInterface
            Instance of the `FileInterface` class.
        """

        self.__Client = None
        self.__FileInterface = file_interface

        self.__host = None
        self.__port = None

    def client_connect(self, host: str, port: str):
        """
        Tries to establish a connection to the Redis instance specified with host and port.

        The established connection is a `StrictRedis` instance and is set as `__Client`.

        Parameters
        ----------
        host : str
            String to identify a host.

        port : str
            String to identify a port.
        """

        self.__Client = redis.StrictRedis(host=host, port=port)
        self.__host = host
        self.__port = port

    def client_disconnect(self):
        """
        Tries to quit the connection to a Redis instance.
        """

        self.__Client.execute_command(QUIT)

        self.__Client = None

    def client_get_connection(self) -> bool:
        """
        Returns the current connection status (True or False).

        For this the response of a `StrictRedis.ping()` call is used.

        Returns
        -------
        bool
            Current connection status.
        """

        try:
            return self.__Client.ping()

        except redis.ConnectionError:
            return False

        except ConnectionRefusedError:
            return False

        except AttributeError:
            return False

    def __query(self, command: str, dbkey: str, report=False) -> list:
        """
        Used to send a OpenCypher query to a Redis instance.

        Calls `StrictRedis.execute_command` with the specified OpenCypher query on the
        specified graph key.

        Parameters
        ----------
        command : str
            A OpenCypher syntax query.

        dbkey : str
            The graph key to query.

        report : bool
            If the response of the query should be reported to the user.

        Returns
        -------
        list
            Encoded query response.
        """

        if self.client_get_connection():

            response = self.__Client.execute_command(G_QUERY, dbkey, command)

            if report:
                self.__show_report(response[1])

            return response[0]

    def db_save(self):
        """
        Sends a save-to-disk request to the connected Redis instance.

        For this the client command `SAVE` is used.
        """

        self.__Client.execute_command('SAVE')

    def db_get_keys(self) -> list:
        """
        Sends a return-keys request to the connected Redis instance.

        For this the client command `KEYS *` is used.

        Returns
        -------
        list
            A list of str. Represents all stored graph keys.
        """

        try:

            # Currently UTF-8 encoded responses are expected.
            return [graph.decode(UTF_8) for graph in self.__Client.execute_command(KEYS)]

        except redis.ResponseError:

            return []

    def db_get_attributes(self) -> tuple:
        """
        Returns all stored properties.

        Tries to return all stored properties of all stored graphs. The
        properties are split into vertex and edge properties.
        """

        # TODO: Inform user about error.
        try:

            ''' Init empty return container.
            '''
            vertex_attributes = []
            edge_attribute = []

            for key in self.db_get_keys():

                try:
                    '''
                    For each graph key query respective properties.
                    Uses the `get_vertex_limited` and `get_edge_limited` functions of the `cypher.py` script.
                    '''
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

    def db_delete_key(self, dbkey: str):
        """
        Sends a delete-key request to the connected Redis instance.

        Parameters
        ----------
        dbkey : str
            The graph-key to delete.
        """

        self.__Client.execute_command(G_DELETE + ' ' + dbkey)

    def db_merge(self, selection: list, source_graphs: list, target_graph: str):
        """
        Calculates the merge graph of a set of source graphs.

        Calculates the merge graph in dependency of a set of selected property names and source graphs.
        The merge graph is built like a union graph, but with unified vertices and edges dependent on their
        values with respect to the selected property names. The following steps are performed:
        1)  Query all possible values of the selected properties.
        2)  Initialize a dictionary for every such value.
            The dictionary is accessible by this value.
        3)  Query all entities (vertices and edges) of the source graphs respective.
        4)  Store all queried vertices in the dictionary accessible by its respective value of the selected
            properties. Add the vertices ID as key to access the dictionary.
        5)  Store all queried edges in the dictionary accessible by its respective source ID.
        6)  For each dictionary create a new vertex/edge that inherits all values of all entities stored
            in the dictionary.
        7)  Rewrite the created vertices and edges as graph into the database.

        Parameters
        ----------
        selection : list
            Specifies the properties for which the merge graph is calculated.
            At index 0 a new merge-property name is stored.

        source_graphs : list
            Specifies the source graphs for which the merge graph is calculated.

        target_graph : str
            The key to store the merge graph with.
        """

        def extract_(entity, *args):

            merge_property_values = set()

            for key in args:

                try:
                    merge_property_values.add(entity[key])

                except KeyError:
                    pass

            merge_property_values.discard('NULL')

            return merge_property_values.pop()

        # Step 1)
        merge_property_name = target_graph + DATA_SEPARATOR + selection.pop(0)

        distinct_values = set()

        for source_graph in source_graphs:
            ''' For each source graph query all values of the properties specified as `selection`.
            '''
            values = set(value.decode(UTF_8) for value in
                         chain.from_iterable(self.__query(get_values(*selection), source_graph)[1:]))
            distinct_values.update(values)
        distinct_values.discard('NULL')

        # Step 2)
        buckets = {}
        index = 0
        for value in distinct_values:
            ''' 
            Each bucket stores:
            - a list of vertices represented as dictionaries.
            - a dictionary to store lists of edges represented as dictionaries.
            - a string, the new ID. 
            '''
            buckets[value] = {VERTEX: [], EDGE: {}, ID: (merge_property_name + str(index))}
            index += 1

        # Step 3)
        response = ([], [])
        vertex_properties = set()
        edge_properties = set()

        for source_graph in source_graphs:

            vertices, edges = \
                self.__split_mapping(
                    self.__response_to_dict(
                        self.__query(get_entities(), source_graph),
                        decode=True
                    )
                )

            vertex_properties.update(list(vertices[0].keys()))
            edge_properties.update(list(edges[0].keys()))

            response[0].extend(vertices)
            response[1].extend(edges)

        # Step 4)
        for vertex in response[0]:
            bucket = buckets[extract_(vertex, *selection)]
            bucket[VERTEX].append(vertex)
            buckets[vertex[ID]] = bucket

        # Step 5)
        for edge in response[1]:
            edge_source = edge[SOURCE]
            edge_target = edge[TARGET]
            edge[SOURCE] = buckets[edge_source][ID]
            edge[TARGET] = buckets[edge_target][ID]
            edge_id = edge[SOURCE] + edge[TARGET]

            bucket = buckets[edge_source]

            if edge_id in bucket[EDGE]:

                bucket[EDGE][edge_id].append(edge)

            else:

                bucket[EDGE][edge_id] = [edge]

        # Step 6)
        # The new graph is represented as two lists of dictionaries.
        graph = {VERTEX: [], EDGE: []}
        for value in distinct_values:

            bucket = buckets[value]

            if bucket[VERTEX]:

                merged_vertex = self.__merge_dictionaries(bucket['vertex'], vertex_properties)
                merged_vertex[ID] = bucket[ID]
                merged_vertex[merge_property_name] = value

                for property_ in selection:
                    merged_vertex[property_] = 'NULL'

                graph[VERTEX].append(merged_vertex)

                for edge_id in bucket[EDGE]:
                    merged_edge = self.__merge_dictionaries(bucket['edge'][edge_id], edge_properties)
                    merged_edge[TARGET] = set(merged_edge[TARGET].split(MERGE_SEPARATOR)).pop()
                    merged_edge[SOURCE] = set(merged_edge[SOURCE].split(MERGE_SEPARATOR)).pop()

                    graph[EDGE].append(merged_edge)

        # Step 7)
        self.db_write(graph, target_graph)

    def db_query(self, query: str, dbkey: str, to_graph=False):
        """
        Executes a query.

        Queries the graph accessed with `dbkey`. If `to_graph` is `True` the
        query-response will be returned.

        Parameters
        ----------
        query : str
            A OpenCypher query.

        dbkey : str
            The key of the graph to query.

        to_graph : bool
            Whether the queries response should be returned.

        Returns
        -------
        tuple optional
            A tuple of two lists of dictionaries. Represents vertices and edges.
        """

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

    def db_explain(self, query: str, dbkey: str):
        """
        Sends a explain-query request to the connected Redis instance.

        Each OpenCypher query has a execution plan.
        This plan can be requested with the `GRAPH.EXPLAIN` command.

        Parameters
        ----------
        query : str
            A OpenCypher query.

        dbkey : str
            The graph-key to delete.

        Returns
        -------
        list
            The encoded execution plan steps.
        """

        return self.__Client.execute_command(G_EXPLAIN, dbkey, query)

    def db_write(self, graph: dict, graph_key: str):
        """
        Stores a graph with the specified key at the connected database.

        The graph has to be specified as a dictionary with the keys vertex and edge.
        Both have to store a list of dictionaries that represent vertices and edges as
        key-value pairs.
        For the upload the redis bulk upload script is used. For this the graph is written
        to a csv file for vertices and edges and a subprocess is called to upload those
        csv files to the database.

        Parameters
        ----------
        graph : dict
            A dictionary storing two lists of dictionaries.

        graph_key : str
            Specifies the graph key to store the graph with.
        """

        self.__FileInterface.write_bulk(graph, graph_key)

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

        finally:

            try:
                remove(nodes)
                remove(edges)

            except FileNotFoundError:
                pass

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
    """
    Comprises methods to read and write files.

    This class is used by the `DataBaseStatus` and `DataBaseInterface` class to read an write files.

    Attributes
    ----------
    __Parser: dict
        Dictionary to store `parser` objects.

    Methods
    -------
    add_parser(key, parser)
        Adds a parser object accessible with a specified key.

    read_header(path, container, mode)
        Reads the header of a graph- or annotation-file and writes the result to a container.

    read_file(instruction, file, mode)
        Reads a file.

    write_file(path, query)
        Writes a query response to a file at path.

    write_bulk(graph, graph_key)
        Writes a graph to csv files ready to be used with the redis bulk upload.
    """

    def __init__(self):

        self.__Parser = {}

    def add_parser(self, key: str, parser: 'Parser'):
        """
        Adds a parser to the classes __Parser attribute.

        Parameters
        ----------
        key : str
            Key to store the `Parser` instance.

        parser : 'Parser'
            The `Parser` instance to store.
        """

        self.__Parser[key] = parser

    def read_header(self, path: str, container: dict, mode: str):
        """
        Reads the header of a file.

        Used to identify the properties stored in a file without parsing the whole file.

        Parameters
        ----------

        path : str
            The path to the file to read,

        container : dict
            Dictionary to store the result.

        mode : str
            One of `parse_graph`, `header_graph`, `parse_annotation`, `header_annotation` to specify the file handling.
        """

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

    def read_file(self, instruction: list, file: tuple, mode: str) -> list or dict:
        """
        Reads a file.

        The files content is handled specified by the `mode` argument. The file should be passed
        as a tuple specifying the file type, name and path.
        Which properties stored in the file should be read can be specified by the instruction argument.

        Parameters
        ----------
        instruction : list
            A list of strings. Specifies the properties to be parsed.

        file : tuple
            Specifies the file type, name and path.

        mode : str
            Specifies which mode for parsing should be used.

        """

        if not type(file) == tuple:
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

    def write_file(self, path: str, query: tuple):
        """
        Writes a query response to a file at path.

        The query response has to be a tuple of two lists of dictionaries specifying vertices and edges
        as key-value pairs.
        For writing files the query is transformed to a iGraph `Graph` object and iGraphs export methods
        are invoked.

        Parameters
        ----------

        path : str
            The path to write the file to.

        query : tuple
            Tuple of two lists specifying the graph to export.
        """

        file_type, file_name = self.__file_info(path)

        if file_type not in ['graphml', 'png']:
            raise FileInterfaceFileTypeException(file_type)

        if file_type == 'graphml':

            self.__write_graphml(self.__create_igraph(query[0], query[1]), path)

        elif file_type == 'png':

            self.__write_png(self.__create_igraph(query[0], query[1]), path)

    @staticmethod
    def write_bulk(graph: dict, graph_key: str):
        """
        Writes a graph to two csv files.

        Uses the redis bulk upload to write a graph into a RedisGraph database.
        The graph has to be specified as dictionary of two lists storing vertices and edges as dictionaries.

        Parameters
        ----------
        graph : dict
            Graph representation as dictionary of two lists.

        graph_key : str
            Used as the key to store the graph.
        """

        vertex_properties = [key for key in graph[VERTEX][0].keys() if key != ID]
        edge_properties = list(graph[EDGE][0].keys())

        path_ = join(abspath(dirname(__file__)), WORK_DIRECTORY)

        with open(path_ + graph_key + '_nodes.csv', 'w+', newline='') as nodes:
            fieldnames = [ID] + vertex_properties
            writer = DictWriter(nodes, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(graph[VERTEX])

        with open(path_ + graph_key + '_edges.csv', 'w+', newline='') as edges:
            fieldnames = [SOURCE, TARGET] + edge_properties
            writer = DictWriter(edges, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(graph[EDGE])

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

        plot(graph, path, bbox=(1000, 1000))

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
