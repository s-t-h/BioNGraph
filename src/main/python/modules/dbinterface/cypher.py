from modules.dbinterface.constants import MATCH, DISTINCT, VERTEX, LIMIT, ONE, EDGE, TARGET, SOURCE


def get_vertex_limited():
    """
    Used to query one vertex.


    This is used to query only one vertex to extract possible properties
    of a graph.

    Returns
    -------
    str
        The constructed OpenCypher query to retrieve one vertex.
    """

    return MATCH + '(' + VERTEX + ')' + DISTINCT + VERTEX + LIMIT + ONE


def get_edge_limited():
    """
    Used to query one edge.


    This is used to query only one edge to extract possible properties
    of a graph.

    Returns
    -------
    str
        The constructed OpenCypher query to retrieve one edge.
    """

    return MATCH + '()-[' + EDGE + ']->()' + DISTINCT + EDGE + LIMIT + ONE


def get_entities():
    """
    Used to query all entities of a graph.

    Returns
    -------
    str
        The constructed OpenCypher query to retrieve all (connected) entities.
    """

    return MATCH + '(' + SOURCE + ')-[' + EDGE + ']->(' + TARGET + ')' + DISTINCT + ', '.join([SOURCE, TARGET, EDGE])


def get_values(*args: str) -> str:
    """
    Used to retrieve all possible values of the properties given in args.

    Parameters
    ----------
    args : str
        Arguments should be only strings.

    Returns
    -------
    str
        The constructed OpenCypher query to retrieve all values of the specified properties.
    """

    return MATCH + '(v)' + DISTINCT + ', '.join(['v.' + arg for arg in args])
