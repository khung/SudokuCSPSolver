# Sudoku CSP Solver

## Description

Sudoku CSP Solver is a tool to visualize how different Constraint Satisfaction
Problem algorithms work using a Sudoku puzzle. The algorithms that can be
visualized are the AC-3 algorithm and the backtracking search algorithm as
described in Chapter 6 of Artificial Intelligence: A Modern Approach (3rd
edition), referred to as AIMA.

For descriptions of the algorithms and their options, see the AIMA textbook.

## Usage

### Running the program

`> python SudokuCSPSolver.py`

### Entering the Sudoku puzzle

![Entering the puzzle](/doc/1_entering_puzzle.png)

The board defaults to a 9 x 9 Sudoku. To change to a 4 x 4 Sudoku, select the
4 x 4 board size.

Click on a cell to enter a value for it.

Click on **Clear all cells** to clear all values.

### Selecting the algorithm options

![Selecting algorithm options](/doc/2_selecting_options.png)

Under Algorithm, select either **Constraint Propagation (AC-3)** or
**Backtracking Search**.

AC-3 does not have any options to configure. For backtracking search, there
are three types of options to configure:

* The heuristic used for selecting the next unassigned variable: the
*Select-Unassigned-Variable* heuristic.
* The heuristic used for selecting the order of the values to consider: the
*Order-Domain-Values* heuristic.
* The inference function used for eliminating domain values.

The minimum-remaining-values (MRV) heuristic will choose the variable that has
the least number of remaining values in its domain. The degree heuristic is a
tie-breaker for the MRV heuristic and will choose the variable that has the
most constraints with the remaining unassigned variables.

The least-constraining-value (LCV) heuristic will order values (in ascending
order) by the number of values removed in the variable's neighbors if that
value is chosen.

Forward checking enforces arc consistency when a variable is assigned, removing
inconsistent values from the domains of the variable's neighbors based on the
constraints.

### Visualizing the algorithm

![Visualizing the algorithm](/doc/3_visualization.png)

Click on **Solve** to run the selected algorithm. After it returns, you
can step through each high-level part of the algorithm.

The step indicator shows the current step and the total number of steps. The
buttons below allow the user to move between the steps. To go to a specific
step, enter a value in the current step and press Enter. The current action
being performed is listed as well.

To go back to the puzzle entry screen, click on **Reset solver**.

#### AC-3

The current domains of all the variables are visible on the board. The
variables that make up the current arc being considered are highlighted on
the board.

The information panel shows the current arc and the current queue.

#### Backtracking search

The domains of all the variables are shown on the board. If an inference
function is used, the domains will be the inferences based on the current
assignment. The current assignment is highlighted in blue on the board. The
current variable being considered is highlighted on the board. The current
value being considered is highlighted in red on the board.

The information panel shows the current assignment, the current variable,
all the values being considered for the variable, and the current value.

## Notes

The 4 x 4 Sudoku board is a Sudoku variant with 2 x 2 regions. The same Sudoku
rules apply as in the original, only with the digits 1-4 instead of 1-9.

For a 9 x 9 Sudoku board, the backtracking search algorithm must use the
MRV heuristic to ensure that the search space is sufficiently small.

Selecting the MRV heuristic will select the forward checking function as
well. The MRV heuristic implicitly requires an inference function to work,
which the forward checking function accomplishes.

As mentioned in AIMA, the degree heuristic is used as a tie-breaker for the
MRV heuristic. Selecting the degree heuristic in the UI will select the MRV
heuristic as well.

Both algorithms can return failure (no consistent assignment). In this case,
the algorithm will be visualized up to the point of failure.

The AC-3 algorithm can return partial assignments if there are domains that
cannot be reduced to one value. This can happen if the puzzle has multiple
solutions or if the puzzle is too difficult for the algorithm.

The backtracking search algorithm can solve Sudoku puzzles that have multiple
solutions. In those cases, only the first solution encountered will be
returned.

It is possible to specify the initial puzzle by entering a string of digits
1-9 (and 0 for empty) as the Python script argument. The string should be
following row-major order (i.e. concatenating each row).

## References
* Russell, Stuart, and Peter Norvig. Artificial Intelligence: A Modern Approach
(3rd Edition). Prentice Hall, 2009.