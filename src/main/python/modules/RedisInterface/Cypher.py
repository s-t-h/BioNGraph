from modules.container.Tags import CREATE, VERTEX, SOURCE, TARGET, ID, EDGE, MATCH, WHERE, AND, NULL, NOT, IS, \
    RETURN, OR, DELETE, SET


def _dict_to_string(dictionary):

        string = """{"""
        last = len(dictionary) - 1

        for index, key in enumerate(dictionary):

            if index == last:
                string = string + key + """:""" + """'""" + dictionary[key] + """'"""
            else:
                string = string + key + """:""" + """'""" + dictionary[key] + """'""" + """, """

        string = string + """}"""

        return string


def _wrap(string):
    return """'""" + string + """'"""


def create_vertex(*args):

    return ''.join(
        map(
            lambda attributes: ' ,(' + attributes[ID] + ':' + VERTEX + ' ' + _dict_to_string(attributes) + ')'
            if args.index(attributes) > 0
            else '(' + attributes[ID] + ':' + VERTEX + ' ' + _dict_to_string(attributes) + ')',
            args
        )
    )


def get_vertex(*args):

    return \
        MATCH + '(v)' \
        + WHERE + OR.join(['v.id' + IS + _wrap(id) for id in args]) \
        + RETURN + 'v'


def get_objects_to_merge(*args):

    return \
        MATCH + '()-[ie]->(v)-[oe]->()' \
        + WHERE + OR.join(['v.id' + IS + _wrap(id) for id in args]) \
        + RETURN + 'v, ie, oe'


def delete_vertex(*args):

    return MATCH + '(v)' + WHERE + '(' + ''.join(
        map(
            lambda identifier: OR + 'v.id' + IS + _wrap(identifier)
            if args.index(identifier) > 0
            else 'v.id' + IS + _wrap(identifier),
            args
        )
    ) + ')' + DELETE + 'v'


def get_vertex_equal(*args):

    nmbr = len(args)

    command = MATCH + ' ' + ', '.join(['(' + 'vertex' + str(index) + ')'
                                       for index in range(nmbr)])

    command += WHERE + 'vertex0.' + args[0] + NOT + NULL

    command += ''.join([AND + 'vertex0.' + args[0]
                        + ' = '
                        + 'vertex' + str(index) + '.'
                        + args[index]
                        for index in range(1, nmbr)])

    command += RETURN + ', '.join(['vertex' + str(index) + '.id'
                                   for index in range(0, nmbr)])

    return command


def get_vertex_limited():

    return MATCH + '(v)' + RETURN + 'v LIMIT 1'


def create_edge(*args):

    return ''.join(
        map(
            lambda attributes: ', (' + attributes[SOURCE] + ')-'
                               + '[:' + EDGE + ' ' + _dict_to_string(attributes) + ']'
                               + '->(' + attributes[TARGET] + ')',
            args
        )
    )


def get_edge(*args):

    return MATCH + '()-[edge]->()' \
           + WHERE + OR.join(['edge.source' + IS + _wrap(id) + OR + 'edge.target' + IS + _wrap(id) for id in args]) \
           + RETURN + 'edge'


def get_edge_limited():

    return MATCH + '()-[edge]->()' + RETURN + 'edge LIMIT 1'


def graph_to_cypher(graph):

    return CREATE + create_vertex(*graph['vertices']) + create_edge(*graph['edges'])


def annotation_dict_to_cypher(dict):

    match = MATCH
    set = SET
    index = 0

    for attribute in dict:

        entries = dict[attribute]

        for entry in entries:

            if index > 0:
                match += ','
                set += ','

            match += ' (v' + str(index) + ' {' + entry[0] + ': ' + _wrap(entry[1]) + '}' ') '

            set += ' v' + str(index) + '.' + attribute + IS + _wrap(entry[2]) + ' '

            index += 1

    return match + set
