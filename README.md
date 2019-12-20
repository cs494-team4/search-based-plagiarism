# Search Based Software Plagiarism

## Requirements

Requires Python version `>=3.6`. 
Get all the other requirements using ```pip install -r requirements.txt``` in the root folder.

## How to Run

In the root folder, edit `runPlagGen.py` line 4 in order to set your project path. Note that a single python file is supported for this version of work. Modification of hyperparameters can be done in `/metaheuristics/GA/GAOptimizer.py` line 18 through 22. 
Then run the file to see tons of refactored codes being stored in /temp. 

```python3 runPlagGen.py```

Running above code will take some time depending on your specifications, and will yield pareto front of the best individuals after it's done.

## Adding new refactorers

- [x] FortoWhile
- [x] SplitAndConditional
- [x] MergeNestedIfStatement
- [x] SplitOrConditional
- [x] AddElseAfterReturnBreakContinue
- [x] StaticToInstance
- [x] MethodPushDown
- [x] PowToOperator
- [x] OperatorToPow
- [x] FormatToStringConcat
- [x] Rename

## Adding new software similarity measurements

We are currently using MOSS(https://theory.stanford.edu/~aiken/moss/) or pycode-similar(https://github.com/fyrestone/pycode_similar.git).

## CustomRefactorer

### Implementing new refactorings

New refactorings should subclass `RefactorOperator` and implement the specified methods
(Look at ForToWhile.py for an example).

You will also need to add the refactorer to the
`_operation_classes`
list in CustomRefactorer.

`test_refactoring.py` can be used to test the implemented refactorings. Change the specified constants at the top of the file to test your implementation.

## Contact

Should you have any kind of problem, please contact us through Issue.
If you like this work, cast a star!
