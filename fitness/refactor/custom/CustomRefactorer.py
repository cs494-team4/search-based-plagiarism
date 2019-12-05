from fitness.refactor.Refactorer import Refactorer
import abc
import astor
import ast
import os
from .operators.ForToWhile import ForToWhile
from .operators.SplitAndConditional import SplitAndConditional
# [In Progress] custom refactorer
# method-level refactoring operators


_operation_classes = {
            "ForToWhile": ForToWhile,
            "SplitAndConditional": SplitAndConditional,
        }

refactored_files_path = 'temp/'


class CustomRefactorer(Refactorer):
    def parse_codebase(self, codebase, *args, **kwargs):
        return astor.parse_file(codebase)

    def __init__(self, codebase):
        super(CustomRefactorer, self).__init__(codebase)

        self.operators = dict()
        self.codebase_repr = self.parse_codebase(codebase)

        # instantiate all refactoring operators
        for _class in _operation_classes:
            self.operators[_class] = _operation_classes[_class](self.codebase_repr)
        self.refactorings = self.retrieve_refactorings()

        if not os.path.exists("temp"):
            os.makedirs("temp")

    def retrieve_refactorings(self):

        refactor_candidates = dict()

        for operator_name in self.operators:
            refactor_candidates[operator_name] = self.operators[operator_name].search_targets()

        return refactor_candidates

    def apply(self, sequence, *args, **kwargs):
        codebase = self.codebase_repr

        for operator_name, target in sequence:
            codebase = self.operators[operator_name].apply(target)

        filename = '{}{}.py'.format(refactored_files_path, id(codebase))
        with open(filename, 'w') as f:
            f.write(astor.to_source(codebase))

        return filename
