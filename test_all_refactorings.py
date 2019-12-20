import py_compile

from fitness.RefactorFitness import RefactorFitness

# Path to the input codebase (singular python file at the moment)
file_path = "codebases/sample1/_classical_simulator.py"
# file_path = "codebases/sample2/sample_original.py"

fit = RefactorFitness(codebase=file_path,
                      refactorer_engine='custom', similarity_client='pycode')
print(f'refactoring_type: {fit.available_refactorings}')

sequence = list()
for refactoring_type in fit.available_refactorings:
    for target in fit.available_refactorings[refactoring_type]:
        sequence.append((refactoring_type, target))

print(f'sequence: {[str(i) + ": " + str(x) for i, x in enumerate(sequence)]}')
print(sequence)
fitness_value = fit([sequence])
suc = fitness_value[0][1]
print(f'suc: {[str(i) + ": " + str(x) for i, x in enumerate(suc)]}')
# py_compile.compile("./temp/result.py", )

print(f'smallest possible plagiarism score: {fitness_value[0][0]}')
