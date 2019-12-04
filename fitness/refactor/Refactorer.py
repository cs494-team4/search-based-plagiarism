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
        generate and return a dictionary with
        {(name_of_refactoring : [list of targets]),...} of all available refactorings

        :return: a list of available refactorings
        """
        pass

    @abc.abstractmethod
    def apply(self, sequence, *args, **kwargs):
        """
        applies a sequence of refactorings to the internal representation of
        the codebase and saves the result to a local directory
        (-> uses unique file names)

        :param sequence: a sequence of refactorings to apply to the codebase [(refactoring_type, target_object)]
        :return: file path to the saved codebase
        """
        pass

    def __init__(self, codebase):
        """
        needs to do
            self.codebase_repr = self.parse_codebase(codebase)
            self.refactorings = self.retrieve_refactorings()
        at one point

        :param codebase: path to codebase
        """
        pass


    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)
