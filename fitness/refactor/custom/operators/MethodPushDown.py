import ast
import astor

from utils import print_node
from .RefactorOperator import RefactorOperator

class MethodPushDown(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.known_classes = {}         # save (class_name, class_node)
        self.pushable_relations = {}    # save (parent_class_name, [id(child_node)])
        self.pushable_methods = {}      # save (id(child_node), method_node)
        self.targets = []               # save id(child_node), which is refactorable child

    def apply(self, target):
        replacer = PushMethodDownToChild(target, self.pushable_methods)
        replacer.walk(self.codebase)
        return self.codebase

    def search_targets(self):
        candidates = list()
        searcher = SearchPushableRelation(self.known_classes, self.pushable_relations, self.pushable_methods, self.codebase)
        searcher.walk(self.codebase)
        searcher.targets = list(self.pushable_methods.keys())
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

class PushMethodDownToChild(astor.TreeWalk):
    def __init__(self, target, pushable_methods):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.pushable_methods = pushable_methods
    
    def pre_ClassDef(self):
        if id(self.cur_node) == self.target:
            child_node = self.cur_node
            ftn = self.pushable_methods[id(child_node)]
            # Check if the child class can have the method pushed down
            canRefactor = True
            for child_body_item in child_node.body:
                # Not a method, skip
                if not isinstance(child_body_item, ast.FunctionDef):
                    continue 
                if child_body_item.name == ftn.name:
                    canRefactor = False
                    break
            if (canRefactor):
                # Push down function
                child_node.body.append(ftn)

class SearchPushableMethod(astor.TreeWalk):
    def __init__(self, target, pushable_relations, pushable_methods):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.pushable_relations = pushable_relations
        self.pushable_methods = pushable_methods
        
    
    def pre_ClassDef(self):
        if id(self.cur_node) == self.target:
            parent_class = self.cur_node
            for body_item in parent_class.body:
                # Not a method, skip
                if not isinstance(body_item, ast.FunctionDef):
                    continue
                # Check if a function is not custom. Ex) Not __init__ function
                if not body_item.name.startswith("__"):
                    # Copy one function of parent_class to child classes
                    # TODO: copy multiple functions of parent_class to child classes
                    for child_id in self.pushable_relations[parent_class.name]:
                        # TODO: check whether child is refactorable with the method **here**, not in refactorer
                        self.pushable_methods[child_id] = body_item
                    break

class SearchPushableRelation(astor.TreeWalk):
    def __init__(self, predefined_classes, pushable_relations, pushable_methods, codebase):
        astor.TreeWalk.__init__(self)
        self.predefined_classes = predefined_classes
        self.pushable_relations = pushable_relations
        self.pushable_methods = pushable_methods
        self.codebase = codebase
        self.targets = []

    def pre_ClassDef(self):
        class_stmt = self.cur_node
        # Save already-defined class def
        self.predefined_classes[class_stmt.name] = id(class_stmt)

        # It's a class; iterate over its BASES(parents)
        for parent_class in class_stmt.bases:
            # Check that if parent is already defined **in the same file**
            # TODO: extend already-defined class scope to imported classes
            if (isinstance(parent_class, ast.Name)
                and parent_class.id in self.predefined_classes):
                    # It's already defined in the same file
                    if not self.pushable_relations:
                        self.pushable_relations[parent_class.id] = [id(class_stmt)]
                    else:
                        self.pushable_relations[parent_class.id].append(id(class_stmt))
                    # TODO: reduce excessive treewalk, if possible
                    srchr = SearchPushableMethod(self.predefined_classes[parent_class.id], self.pushable_relations, self.pushable_methods)
                    srchr.walk(self.codebase)

            