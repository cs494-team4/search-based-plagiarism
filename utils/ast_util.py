import astor


def print_node(node):
    print(astor.to_source(node))


def print_nodes(node_list):
    [print_node(node) for node in node_list]
