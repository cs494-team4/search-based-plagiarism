import astor


def print_node(node):
    print(astor.to_source(node))
