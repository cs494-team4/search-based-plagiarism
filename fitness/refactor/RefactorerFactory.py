from fitness.refactor.rope.Rope import Rope
from fitness.refactor.test_dummy.Dummy import Dummy
from fitness.refactor.custom.CustomRefactorer import CustomRefactorer


class RefactorerFactory:

    __refactorer_classes = {
        "rope": Rope,
        "test_dummy": Dummy,
        "custom": CustomRefactorer
    }

    @staticmethod
    def create(name, *args, **kwargs):
        refactorer_class = RefactorerFactory.__refactorer_classes.get(
            name.lower(), None)

        if refactorer_class:
            return refactorer_class(*args, **kwargs)
        raise NotImplementedError(
            "The refactorer "+str(name)+" is not implemented")
