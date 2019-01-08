import igraph
import copy
from modules.container.Tags import MERGE_SEPARATOR


class Graph:

    def __init__(self):

        self.__Vid = set()
        self.Vertices = []

        self.__Eid = set()
        self.Edges = []

    def __str__(self):

        response = ''

        response += '#Vertices: {} \n'.format(len(self.Vertices))
        for vertex in self.Vertices:
            response += str(vertex) + '\n'

        response += '#Edges: {} \n'.format(len(self.Edges))
        for edge in self.Edges:
            response += str(edge) + '\n'

        return response

    def add_vertex(self, vertex):

        try:
            iid = vertex['id']

            if iid not in self.__Vid:

                self.__Vid.add(iid)
                self.Vertices.append(vertex)

        except KeyError:
            raise Exception('Vertices have to contain a id attribute.')

    def add_edge(self, edge):

        try:
            iid = edge['source'] + edge['target']

            if iid not in self.__Eid:

                self.__Eid.add(iid)
                self.Edges.append(edge)

        except KeyError:
            raise Exception('Vertices have to contain a id attribute.')

    def __create_igraph(self):

        g = igraph.Graph()
        vertices = copy.deepcopy(self.Vertices)
        edges = copy.deepcopy(self.Edges)

        for vertex in vertices:

            iid = vertex.pop('id')

            for key in vertex.keys():

                values = set(vertex[key].split(MERGE_SEPARATOR))
                values.discard('NULL')

                if values:

                    vertex[key] = ';'.join(values)

                else:

                    vertex[key] = None

            g.add_vertex(name=iid, **vertex)

        for edge in edges:
            source = edge.pop('source')
            target = edge.pop('target')

            for key in edge.keys():
                values = set(edge[key].split(MERGE_SEPARATOR))
                values.discard('NULL')
                edge[key] = ';'.join(values)

            g.add_edge(source, target, **edge)

        del g.vs['name']

        return g

    def save_as_graphml(self, file):

        self.__create_igraph().write_graphml(f=file)

    def save_as_png(self, file):

        ig = self.__create_igraph()

        vertex_color_map = {}
        edge_color_map = {}

        for property_count, color_map in [(len(ig.vertex_attributes()), vertex_color_map),
                                          (len(ig.edge_attributes()), edge_color_map)]:

            rgb_fraction = round(255 / max(1, property_count))

            for count in range(property_count + 1):

                color_map[count] = ', '.join([str(min(255, 0 + rgb_fraction * count)),
                                              str(200),
                                              str(max(0, 255 - rgb_fraction * count))])

        visual_style = {
            'vertex_color': [vertex_color_map[len([attribute for attribute in vertex.attributes().values() if attribute])] for vertex in ig.vs],
            'edge_color': [edge_color_map[len([attribute for attribute in edge.attributes().values() if attribute])] for edge in ig.es]
        }

        igraph.plot(ig, file, **visual_style)
