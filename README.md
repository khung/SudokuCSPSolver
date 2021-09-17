# Sudoku CSP Solver

## Description

Sudoku CSP Solver is a tool to visualize how different Constraint Satisfaction
Problem algorithms work using a Sudoku puzzle. The algorithms that can be
visualized are the AC-3 algorithm and the backtracking search algorithm as
described in Chapter 6 of Artificial Intelligence: A Modern Approach (AIMA).

For descriptions of the algorithms and their options, see the AIMA textbook.

## Usage

### Running the program

> python SudokuCSPSolver.py

### Entering the Sudoku puzzle

![Entering the puzzle](/doc/1_entering_puzzle.png)

### Selecting the algorithm options

### Visualizing the algorithm

## Notes

The 4 x 4 Sudoku board is a Sudoku variant with 2 x 2 regions. The same Sudoku
rules apply as in the original, only with the digits 1 - 4 instead of 1 - 9.

For a 9 x 9 Sudoku board, the backtracking search algorithm must use the
MRV heuristic to ensure that the search space is sufficiently small.

Selecting the MRV heuristic in the UI will select the forward checking
heuristic as well. The MRV heuristic implicitly requires an inference function
to work, which the forward checking heuristic accomplishes.

As mentioned in AIMA, the degree heuristic is used as a tie-breaker for the
MRV heuristic. Selecting the degree heuristic in the UI will select the MRV
heuristic as well.

Both algorithms can return failure (no consistent assignment). In this case,
the algorithm will still be visualized up to the failure point.

The AC-3 algorithm can return partial assignments if there are domains that
cannot be reduced to one value. Also, the algorithm is not sufficiently
powerful to solve all Sudoku puzzles. In those cases, it will return a partial
assignment.

The backtracking search algorithm can solve Sudoku puzzles that have multiple
solutions. In those cases, only the first solution encountered will be
returned.

It is possible to specify the initial puzzle by entering a string of digits
1 - 9 (and 0 for empty) as the Python script argument. The string should be
following row-major order (i.e. concatenating each row).

## References
* Russell, Stuart, and Peter Norvig. Artificial Intelligence: A Modern Approach
(3rd Edition). Prentice Hall, 2009.