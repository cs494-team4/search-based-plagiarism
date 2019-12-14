import astor
import ast


def print_node(node):
    print(astor.to_source(node))


def print_nodes(node_list):
    [print_node(node) for node in node_list]


def dump_node(node, text=""):
    if not text:
        print(f'{ast.dump(node)}')
    else:
        print(f'{text}: {ast.dump(node)}')
