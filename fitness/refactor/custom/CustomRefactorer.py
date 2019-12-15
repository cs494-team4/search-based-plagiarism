import os

import astor

from fitness.refactor.Refactorer import Refactorer
from .operators.AddElseAfterReturnBreakContinue import AddElseAfterReturnBreakContinue
from .operators.ExprToNaryFunc import ExprToNaryFunc
from .operators.FillInDefaultArguments import FillInDefaultArguments
from .operators.ForToWhile import ForToWhile
from .operators.FormatToStringConcat import FormatToStringConcat
from .operators.MergeNestedIfStatement import MergeNestedIfStatement
from .operators.MethodPushDown import MethodPushDown
from .operators.OperatorToPow import OperatorToPow
from .operators.PowToOperator import PowToOperator
from .operators.SplitAndConditional import SplitAndConditional
from .operators.SplitOrConditional import SplitOrConditional
from .operators.StaticToInstance import StaticToInstance

# [In Progress] custom refactorer
# method-level refactoring operators


_operation_classes = {
    "ForToWhile": ForToWhile,
    "SplitAndConditional": SplitAndConditional,
    "MergeNestedIfStatement": MergeNestedIfStatement,
    "SplitOrConditional": SplitOrConditional,
    "AddElseAfterReturnBreakContinue": AddElseAfterReturnBreakContinue,
    "StaticToInstance": StaticToInstance,
    "MethodPushDown": MethodPushDown,
    "PowToOperator": PowToOperator,
    "OperatorToPow": OperatorToPow,
    "FillInDefaultArguments": FillInDefaultArguments,
    # "FormatToStringConcat": FormatToStringConcat,
    # "Rename": Rename,
    "FormatToStringConcat": FormatToStringConcat,
    "ExprToNaryFunc": ExprToNaryFunc

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
            self.operators[_class] = \
                _operation_classes[_class](self.codebase_repr)
        self.refactorings = self.retrieve_refactorings()

        if not os.path.exists(refactored_files_path):
            os.makedirs(refactored_files_path)

    def retrieve_refactorings(self):
        refactor_candidates = dict()

        for operator_name in self.operators:
            refactor_candidates[operator_name] = \
                self.operators[operator_name].search_targets()

        return refactor_candidates

    def apply(self, sequence, *args, **kwargs):
        codebase = self.codebase_repr
        success_indicies = list()

        for operator_name, target in sequence:
            codebase, success = self.operators[operator_name].apply(target)
            success_indicies.append(success)

        filename = '{}{}.py'.format(refactored_files_path, "result")  # id(codebase))
        with open(filename, 'w') as f:
            # print(astor.dump_tree(codebase))
            f.write(astor.to_source(codebase))

        return filename, success_indicies
