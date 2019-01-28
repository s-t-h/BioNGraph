from modules.old.Tags import CREATE, VERTEX, SOURCE, TARGET, ID, EDGE, MATCH, WHERE, AND, NULL, NOT, IS, \
    DISTINCT, OR, DELETE, SET, DATA_SEPARATOR, RETURN


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


def create_vertex(*args, label_=VERTEX):

    return ''.join(
        map(
            lambda attributes: ' ,(' + attributes[ID] + ':' + label_ + ' ' + _dict_to_string(attributes) + ')'
            if args.index(attributes) > 0
            else '(' + attributes[ID] + ':' + label_ + ' ' + _dict_to_string(attributes) + ')',
            args
        )
    )

'''
def get_vertex(*args):

    return \
        MATCH + '(v)' \
        + WHERE + OR.join(['v.id' + IS + _wrap(id) for id in args]) \
        + RETURN + 'v'
'''

'''
def get_objects_to_merge(*args):

    return \
        MATCH + '()-[ie]->(v)-[oe]->()' \
        + WHERE + OR.join(['v.id' + IS + _wrap(id) for id in args]) \
        + RETURN + 'v, ie, oe'
'''


def delete_vertex(*args):

    return MATCH + '(v)' + WHERE + '(' + ''.join(
        map(
            lambda identifier: OR + 'v.id' + IS + _wrap(identifier)
            if args.index(identifier) > 0
            else 'v.id' + IS + _wrap(identifier),
            args
        )
    ) + ')' + DELETE + 'v'


'''
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
'''


def get_vertex_limited():

    return MATCH + '(v)' + DISTINCT + 'v LIMIT 1'


def create_edge(*args, type_=EDGE):

    return ''.join(
        map(
            lambda attributes: ', (' + attributes[SOURCE] + ')-'
                               + '[:' + type_ + ' ' + _dict_to_string(attributes) + ']'
                               + '->(' + attributes[TARGET] + ')',
            args
        )
    )


'''
def get_edge(*args):

    return MATCH + '()-[edge]->()' \
           + WHERE + OR.join(['edge.target' + IS + _wrap(id) for id in args]) \
           + RETURN + 'edge'
'''


def get_edge_limited():

    return MATCH + '()-[edge]->()' + DISTINCT + 'edge LIMIT 1'


def get_merge_entities(*args):

    return \
        MATCH + '(v)-[e]->(w)' + \
        WHERE + OR.join(['v.' + arg + NOT + NULL for arg in args]) + \
        OR + OR.join(['w.' + arg + NOT + NULL for arg in args]) + \
        DISTINCT + 'v, w, e'


def get_merge_values(*args):

    return MATCH + '(v)' + RETURN + ', '.join(['v.' + arg for arg in args])


def graph_to_cypher(graph, label_=VERTEX, type_=EDGE):

    return CREATE + create_vertex(*graph['vertices'], label_=label_) + create_edge(*graph['edges'], type_=type_)


def annotation_dict_to_cypher(target_property, map_property, property_prefix, dictionaries):

    # TODO: If not all Vertices are matched, no property is set... Try atomic queries instead.

    match = MATCH
    set = SET
    dictionary_index = 0

    for dictionary in dictionaries:

        if dictionary_index > 0:

            match += ','
            set += ','

        match += ' (v' + str(dictionary_index) + ' {' + target_property + ': ' + _wrap(dictionary.pop(map_property)) + '}' ') '

        property_index = 0

        for key, value in dictionary.items():

            if property_index > 0:

                set += ','

            set += ' v' + str(dictionary_index) + '.' + property_prefix + DATA_SEPARATOR + key + IS + _wrap(value) + ' '

            property_index += 1

        dictionary_index += 1

    print(match + set)

    return match + set
