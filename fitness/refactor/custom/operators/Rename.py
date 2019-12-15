import ast

import astor

from .RefactorOperator import RefactorOperator


# rename variable, class, function name


class Rename(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = Renamer(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchVar()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        # print() is a function identifier but should not be selected as a candidate
        return isinstance(node, ast.Name) and node.id not in dir(__builtins__)


class Renamer(astor.TreeWalk):
    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_Name(self):
        if id(self.cur_node) == self.target and Rename.is_applicable(self.cur_node):
            # random_string = randomString(4);
            new_name = "new_" + self.cur_node.id
            new_node = ast.Name(id=new_name, ctx=self.cur_node.ctx)
            self.replace(new_node)
            self.applied = True


class SearchVar(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Name(self):
        if Rename.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))
            # self.targets.append(self.cur_node.id)

    def pre_ClassDef(self):
        if Rename.is_applicable(self.cur_node.name):
            self.targets.append(id(self.cur_node.name))

    def pre_FunctionDef(self):
        if Rename.is_applicable(self.cur_node.name):
            self.targets.append(id(self.cur_node.name))

# # Generate a random string of fixed length
# def randomString(stringLength):
#     letters = string.ascii_lowercase
#     return ''.join(random.choice(letters) for i in range(stringLength))
