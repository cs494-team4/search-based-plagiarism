import astor
from .RefactorOperator import RefactorOperator


class ChangeOrderOfParameters(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = OrderOfParametersChanger(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchOrderChangeableParameters()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    # todo: rethink is_applicable
    @staticmethod
    def is_applicable(node):
        return len(node.args.args) >= 2


class OrderOfParametersChanger(astor.TreeWalk):
    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target_id = target
        self.target_ref = ''

        self.calls = []
        self.applied = False

    def pre_Call(self):
        # print(f'def: {ast.dump(self.target_ref)}')
        if self.cur_node.func.id == self.target_ref.name:
            node = self.cur_node
            node.args.reverse()

    # search for a function definition
    def pre_FunctionDef(self):
        if id(self.cur_node) == self.target_id \
                and ChangeOrderOfParameters.is_applicable(self.cur_node):
            self.applied = True
            node = self.cur_node
            self.target_ref = node
            node.args.args.reverse()
            node.args.defaults.reverse()
            # currently only reversing


class SearchOrderChangeableParameters(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    # search for a function definition
    # with at least 2 parameters
    # todo: exclude "edge" cases
    def pre_FunctionDef(self):
        node = self.cur_node
        if len(node.args.args) >= 2 \
                and node.args.vararg is None:
            self.targets.append(id(node))
