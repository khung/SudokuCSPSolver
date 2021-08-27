from algorithms import ConstraintSatisfactionProblem


class SudokuBoard:
    def __init__(self, initial_values: list = None):
        self.board = [[0 for i in range(9)] for i in range(9)]
        if initial_values:
            if len(initial_values) != 9*9:
                raise ValueError("initial_values must contain {} items".format(9*9))
            old_board = self.board.copy()
            for i in range(9):
                for j in range(9):
                    self.board[i][j] = initial_values[i*9 + j]
            if not self._is_valid():
                self.board = old_board
                raise ValueError("initial_values contains an invalid Sudoku puzzle")

    def set_cells(self, values: list):
        if len(values) != 9*9:
            raise ValueError("initial_values must contain {} items".format(9*9))
        old_board = self.board.copy()
        for i in range(9):
            for j in range(9):
                self.board[i][j] = values[i*9 + j]
        if not self._is_valid():
            self.board = old_board
            raise ValueError("initial_values contains an invalid Sudoku puzzle")

    def _is_valid(self, cell: tuple = None) -> bool:
        # Check that all cell values are valid per Sudoku rules
        # Lookup what group an index is in to see its corresponding region
        index_groups = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

        row_range = [i for i in range(9)]
        col_range = [i for i in range(9)]
        if cell:
            # If cell is passed in, we only check the validity of that cell
            row_range = [cell[0]]
            col_range = [cell[1]]
        for i in row_range:
            row_group_indices = index_groups[i // 3]
            for j in col_range:
                first_value = self.board[i][j]
                # Don't check if cell is empty
                if first_value == 0:
                    continue
                # Check rows
                for k in range(j+1, 9):
                    second_value = self.board[i][k]
                    if first_value == second_value:
                        return False
                # Check columns
                for k in range(i+1, 9):
                    second_value = self.board[k][j]
                    if first_value == second_value:
                        return False
                # Check region
                col_group_indices = index_groups[j // 3]
                for m in row_group_indices:
                    for n in col_group_indices:
                        if m != i and n != j:
                            second_value = self.board[m][n]
                            if first_value == second_value:
                                return False
        return True

    def to_list(self) -> list:
        result = []
        for i in range(9):
            result.extend(self.board[i])
        return result

    def get_cell_value(self, row, column):
        value = self.board[row][column]
        # Don't return 0 (empty cell)
        if value == 0:
            value = None
        return value

    def generate_csp(self) -> ConstraintSatisfactionProblem:
        variables = []
        domains = []
        for i in range(9):
            for j in range(9):
                # Add variables as 11, 12, ..., 98, 99
                variables.append(str((i+1)*10 + (j+1)))
                cell_value = self.get_cell_value(i, j)
                # If there's a value, the domain is just that value. Otherwise, the initial domain is all digits 1-9
                if cell_value:
                    domains.append([cell_value])
                else:
                    domains.append([i for i in range(1, 10)])
        constraints = []

        def not_equal(v1, v2):
            return v1 != v2
        # Lookup what group an index is in to see its corresponding region
        index_groups = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        for i in range(1, 10):
            row_group_indices = index_groups[(i-1)//3]
            for j in range(1, 10):
                first_var = str(i*10 + j)
                # AllDiff on rows
                for k in range(j+1, 10):
                    second_var = str(i*10 + k)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on columns
                for k in range(i+1, 10):
                    second_var = str(k*10 + j)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on regions
                # This will have duplicates but the CSP class should take care of it when considering the constraints
                col_group_indices = index_groups[(j-1)//3]
                for m in row_group_indices:
                    for n in col_group_indices:
                        if m != i and n != j:
                            second_var = str(m*10 + n)
                            constraints.append((first_var, second_var, not_equal))
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        return csp
