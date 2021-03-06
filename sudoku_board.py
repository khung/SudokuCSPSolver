from algorithms import ConstraintSatisfactionProblem
from typing import Optional


class SudokuBoard:
    """
    A Sudoku board, either 9x9 or 4x4 in size.

    Public methods
    --------------
    * set_cells
    * to_list
    * get_cell_value
    * generate_csp
    * make_variable_name
    * get_row_col_from_variable_name

    Instance variables
    ------------------
    * size
    * board
    """
    board_sizes = [4, 9]

    def __init__(self, initial_values: Optional[list] = None, size: int = 9) -> None:
        """
        :param initial_values: An optional list of initial values to populate the Sudoku board. 0 is used to indicate
        an empty cell.
        :param size: The size of the Sudoku board (9 or 4).
        """
        if size not in SudokuBoard.board_sizes:
            raise ValueError("Invalid value for size")
        self.size = size
        self.board = [[0 for i in range(self.size)] for i in range(self.size)]
        if initial_values:
            if len(initial_values) != self.size*self.size:
                raise ValueError("initial_values must contain {} items".format(self.size*self.size))
            for i in range(self.size):
                for j in range(self.size):
                    self.board[i][j] = initial_values[i*self.size + j]
            if not self._is_valid():
                raise ValueError("initial_values contains an invalid Sudoku puzzle")

    def set_cells(self, values: list) -> None:
        """
        Set the values of all cells on the board.

        :param values: The list of values to set.
        """
        if len(values) != self.size*self.size:
            raise ValueError("initial_values must contain {} items".format(self.size*self.size))
        old_board = self.board.copy()
        for i in range(self.size):
            for j in range(self.size):
                self.board[i][j] = values[i*self.size + j]
        if not self._is_valid():
            self.board = old_board
            raise ValueError("initial_values contains an invalid Sudoku puzzle")

    def _is_valid(self, cell: Optional[tuple] = None) -> bool:
        # Check that all cell values are valid per Sudoku rules
        # Lookup what group an index is in to see its corresponding region
        if self.size == 9:
            num_groups = 3
            index_groups = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        elif self.size == 4:
            num_groups = 2
            index_groups = [[0, 1], [2, 3]]
        else:
            raise ValueError("Invalid value used for size")

        row_range = [i for i in range(self.size)]
        col_range = [i for i in range(self.size)]
        if cell:
            # If cell is passed in, we only check the validity of that cell
            row_range = [cell[0]]
            col_range = [cell[1]]
        for i in row_range:
            row_group_indices = index_groups[i // num_groups]
            for j in col_range:
                first_value = self.board[i][j]
                # Don't check if cell is empty
                if first_value == 0:
                    continue
                # Check rows
                for k in range(j+1, self.size):
                    second_value = self.board[i][k]
                    if first_value == second_value:
                        return False
                # Check columns
                for k in range(i+1, self.size):
                    second_value = self.board[k][j]
                    if first_value == second_value:
                        return False
                # Check region
                col_group_indices = index_groups[j // num_groups]
                for m in row_group_indices:
                    for n in col_group_indices:
                        if m != i and n != j:
                            second_value = self.board[m][n]
                            if first_value == second_value:
                                return False
        return True

    def to_list(self) -> list:
        """
        Create a list of the board values.

        :return: List of all board values in row-major order.
        """
        result = []
        for i in range(self.size):
            result.extend(self.board[i])
        return result

    def get_cell_value(self, row: int, column: int) -> int:
        """
        Get the value of a cell.

        :param row: The row of the cell.
        :param column: The column of the cell.
        :return: The value of the cell (None if empty).
        """
        value = self.board[row][column]
        # Don't return 0 (empty cell)
        if value == 0:
            value = None
        return value

    def generate_csp(self) -> ConstraintSatisfactionProblem:
        """
        Create a constraint satisfaction problem from the Sudoku board.

        :return: The CSP of the Sudoku board.
        """
        variables = []
        domains = []
        for i in range(self.size):
            for j in range(self.size):
                # Add variables as 1-1, 1-2, ..., 9-8, 9-9
                variables.append(self.make_variable_name(i+1, j+1))
                cell_value = self.get_cell_value(i, j)
                # If there's a value, the domain is just that value. Otherwise, the initial domain is all digits 1-9
                if cell_value:
                    domains.append([cell_value])
                else:
                    domains.append([i for i in range(1, self.size+1)])
        constraints = []

        def not_equal(v1, v2):
            return v1 != v2
        # Lookup what group an index is in to see its corresponding region
        if self.size == 9:
            num_groups = 3
            index_groups = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        elif self.size == 4:
            num_groups = 2
            index_groups = [[1, 2], [3, 4]]
        else:
            raise ValueError("Invalid value used for size")
        for i in range(1, self.size+1):
            row_group_indices = index_groups[(i-1)//num_groups]
            for j in range(1, self.size+1):
                first_var = self.make_variable_name(i, j)
                # AllDiff on rows
                for k in range(j+1, self.size+1):
                    second_var = self.make_variable_name(i, k)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on columns
                for k in range(i+1, self.size+1):
                    second_var = self.make_variable_name(k, j)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on regions
                # This will have duplicates but the CSP class should take care of it when considering the constraints
                col_group_indices = index_groups[(j-1)//num_groups]
                for m in row_group_indices:
                    for n in col_group_indices:
                        if m != i and n != j:
                            second_var = self.make_variable_name(m, n)
                            constraints.append((first_var, second_var, not_equal))
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        return csp

    @staticmethod
    def make_variable_name(i: int, j: int) -> str:
        """
        Create the name of the variable in position (i, j) where both i and j start at 1.

        :param i: Row portion of the variable name.
        :param j: Column portion of the variable name.
        :return: The variable name at the specified position.
        """
        # Starts from 1, 1
        return str(i) + '-' + str(j)

    @staticmethod
    def get_row_col_from_variable_name(variable_name: str) -> (int, int):
        """
        Get the row and column of the variable name given, starting at index 1.

        :param variable_name: The variable name to look up.
        :return: The row and column of the variable.
        """
        # Starts from 1, 1
        strings = variable_name.split('-')
        return int(strings[0]), int(strings[1])
