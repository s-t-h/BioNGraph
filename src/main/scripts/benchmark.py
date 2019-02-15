import sys

from igraph import Graph
from string import ascii_uppercase, digits
from random import choices, choice, randint
from time import time

from modules.dbinterface.interface import FileInterface, DataBaseInterface


class Benchmark:
    """
    Benchmarking on random networks.

    Used to analyze the runtime of BioNGraph on random networks.
    For this purpose random networks are created with the Barabasi-Albert-Model implementation of iGraph.
    """

    def __init__(self, file_interface, db_interface):

        self.__FileInterface = fileInterface
        self.__DBInterface = db_interface

        self.__selection = ['merged', 'label']

        self.__PoolGraphs = []

        self.__DBInterface.client_connect(host='localhost', port='6379')

    @staticmethod
    def __generate_random_graph(node_count, edge_count, power_coeff=1.5):
        """

        """

        g = Graph.Barabasi(n=node_count, m=edge_count, power=power_coeff, directed=True, outpref=True)

        identifiers = [''.join(choices(ascii_uppercase + digits, k=10)) for index in range(0, node_count)]

        graph = {'vertices': [], 'edges': []}

        for v in g.vs:
            identifier = choice(identifiers)
            graph['vertices'].append({'id': str(v.index), 'label': identifier})

        for e in g.es:
            graph['edges'].append({'source': str(e.source), 'target': str(e.target)})

        return graph

    def generate_graph_pool(self, graph_count=1, node_count=1000, edge_count=randint(3, 10), power_coeff=1.5):

        keys = [''.join(choices(ascii_uppercase, k=8)) for index in range(0, graph_count)]

        self.__PoolGraphs = [(keys[index], self.__generate_random_graph(node_count, edge_count, power_coeff))
                             for index in range(0, graph_count)]

        for key, graph in self.__PoolGraphs:

            self.__DBInterface.db_write(graph, key)

    def clean_database(self):

        for key, graph in self.__PoolGraphs:

            self.__DBInterface.db_delete_key(key)

        self.__DBInterface.client_disconnect()

    def run(self, merge_count=2):

        graph_keys = [key[0] for key in choices(self.__PoolGraphs, k=merge_count)]
        target_key = ''.join(choices(ascii_uppercase, k=6))

        start = time()
        self.__DBInterface.db_merge(self.__selection, list(graph_keys), target_key)
        end = time()

        t = end - start

        self.__DBInterface.db_delete_key(target_key)

        return t

    @staticmethod
    def print_results(text, t, path):

        with open(path + 'times' + '.txt', 'a+') as file:

            file.write(text + ' : ' + str(t) + '\n')

            file.close()


if __name__ == '__main__':

    fileInterface = FileInterface()
    databaseInterface = DataBaseInterface(fileInterface)
    benchmark = Benchmark(fileInterface, databaseInterface)

    '''
    - Number of nodes to create.
    - Number of edges to create per node.
    - Number of networks to create.
    - The path to write the result.
    '''
    nodes, edges, power, count, path = sys.argv[1:]

    benchmark.generate_graph_pool(int(count), int(nodes), int(edges), float(power))

    benchmark.print_results(
        path,
        nodes + '__' + count,
        benchmark.run(int(count))
    )

    benchmark.clean_database()
