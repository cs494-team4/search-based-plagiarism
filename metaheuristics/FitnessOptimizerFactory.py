from metaheuristics.GA.GAOptimizer import GAOptimizer


class FitnessOptimizerFactory:

    __optimizer_classes = {
        "ga": GAOptimizer,
    }

    @staticmethod
    def create(name, *args, **kwargs):
        optimizer_class = FitnessOptimizerFactory.__optimizer_classes.get(
            name.lower(), None)

        if optimizer_class:
            return optimizer_class(*args, **kwargs)
        raise NotImplementedError(
            "The fitness optimizer "+str(name)+" is not implemented")
