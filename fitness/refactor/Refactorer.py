import abc


class Refactorer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_codebase(self, codebase, *args, **kwargs):
        """
        reads in a codebase from the file system and converts it into an
        internal representation of the codebase for the refactorer

        :param codebase: location of the codebase to read in
        :return: internal representation of the codebase
        """
        pass

    @abc.abstractmethod
    def retrieve_refactorings(self):
        """
        generate and return a list of available refactorings offered by the
        refactoring framework
        # TODO find general representation based on refactoring framework

        :return: a list of available refactorings
        """
        pass

    @abc.abstractmethod
    def apply(self, sequence, *args, **kwargs):
        """
        applies a sequence of refactorings to the internal representation of
        the codebase and saves the result to a local directory
        (-> uses unique file names)

        :param sequence: a sequence of refactorings to apply to the codebase
        :return: file path to the saved codebase
        """
        pass

    def __init__(self, codebase):
        self.codebase_repr = self.parse_codebase(codebase)
        self.refactorings = self.retrieve_refactorings()

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)
