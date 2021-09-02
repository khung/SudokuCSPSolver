from algorithms import ConstraintSatisfactionProblem


class SudokuBoard:
    board_sizes = [4, 9]

    def __init__(self, initial_values: list = None, size: int = 9):
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

    def set_cells(self, values: list):
        if len(values) != self.size*self.size:
            raise ValueError("initial_values must contain {} items".format(self.size*self.size))
        old_board = self.board.copy()
        for i in range(self.size):
            for j in range(self.size):
                self.board[i][j] = values[i*self.size + j]
        if not self._is_valid():
            self.board = old_board
            raise ValueError("initial_values contains an invalid Sudoku puzzle")

    def _is_valid(self, cell: tuple = None) -> bool:
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
        result = []
        for i in range(self.size):
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
        for i in range(self.size):
            for j in range(self.size):
                # Add variables as 11, 12, ..., 98, 99
                variables.append(str((i+1)*10 + (j+1)))
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
                first_var = str(i*10 + j)
                # AllDiff on rows
                for k in range(j+1, self.size+1):
                    second_var = str(i*10 + k)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on columns
                for k in range(i+1, self.size+1):
                    second_var = str(k*10 + j)
                    constraints.append((first_var, second_var, not_equal))
                # AllDiff on regions
                # This will have duplicates but the CSP class should take care of it when considering the constraints
                col_group_indices = index_groups[(j-1)//num_groups]
                for m in row_group_indices:
                    for n in col_group_indices:
                        if m != i and n != j:
                            second_var = str(m*10 + n)
                            constraints.append((first_var, second_var, not_equal))
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        return csp
