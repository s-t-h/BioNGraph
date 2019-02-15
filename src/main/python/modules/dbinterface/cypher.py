from modules.old.Tags import CREATE, VERTEX, SOURCE, TARGET, ID, EDGE, MATCH, WHERE, IS, \
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


def delete_vertex(*args):

    return MATCH + '(v)' + WHERE + '(' + ''.join(
        map(
            lambda identifier: OR + 'v.id' + IS + _wrap(identifier)
            if args.index(identifier) > 0
            else 'v.id' + IS + _wrap(identifier),
            args
        )
    ) + ')' + DELETE + 'v'


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


def get_edge_limited():

    return MATCH + '()-[edge]->()' + DISTINCT + 'edge LIMIT 1'


def get_merge_entities():

    return \
        MATCH + '(v)-[e]->(w)' + \
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
