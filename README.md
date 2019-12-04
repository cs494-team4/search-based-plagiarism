# Search Based Software Plagiarism

## Adding new refactorers
 TODO
## Adding new software similarity measurements
 TODO


## CustomRefactorer

### Implementing new refactorings

New refactorings should subclass `RefactorOperator` and implement the specified methods
(Look at ForToWhile.py for an example).

You will also need to add the refactorer to the 
`_operation_classes`
list in CustomRefactorer.

`test_refactoring.py` can be used to test the implemented refactorings. Change the specified constants at the top of the file to test your implementation.
