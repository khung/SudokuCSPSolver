import unittest
from sudoku_board import *


class TestSudokuBoard(unittest.TestCase):
    def test_create_sudoku_empty(self):
        board = SudokuBoard()
        self.assertTrue(type(board) is SudokuBoard)
        for i in range(9):
            for j in range(9):
                self.assertIsNone(board.get_cell_value(i, j))

    def test_create_sudoku_with_values(self):
        values = []
        for i in range(9):
            if i == 0:
                values.extend([j for j in range(1, 10)])
            else:
                values.extend([0 for j in range(9)])
        board = SudokuBoard(initial_values=values)
        for i in range(9):
            for j in range(9):
                value = board.get_cell_value(i, j)
                if value is None:
                    value = 0
                self.assertEqual(values[i*9 + j], value)

    def test_set_values(self):
        values = []
        for i in range(9):
            if i == 0:
                values.extend([j for j in range(1, 10)])
            else:
                values.extend([0 for j in range(9)])
        board = SudokuBoard()
        board.set_cells(values=values)
        for i in range(9):
            for j in range(9):
                value = board.get_cell_value(i, j)
                if value is None:
                    value = 0
                self.assertEqual(values[i*9 + j], value)

    def test_to_list(self):
        values = []
        for i in range(9):
            if i == 0:
                values.extend([j for j in range(1, 10)])
            else:
                values.extend([0 for j in range(9)])
        board = SudokuBoard(initial_values=values)
        self.assertListEqual(values, board.to_list())

    def assert_correct_CSP(self, values, size=9):
        board = SudokuBoard(initial_values=values, size=size)
        if values is None:
            values = [0 for i in range(size*size)]
        csp = board.generate_csp()
        variables = []
        for i in range(1, size+1):
            for j in range(1, size+1):
                variables.append(str(i * 10 + j))
        self.assertEqual(variables, csp.variables)
        domain = [i for i in range(1, size+1)]
        for i in range(size):
            for j in range(size):
                var_name = str((i+1) * 10 + (j+1))
                value_index = i*size + j
                reference_value = values[value_index]
                if reference_value != 0:
                    self.assertEqual([reference_value], csp.get_domain(var_name))
                else:
                    self.assertEqual(domain, csp.get_domain(var_name))
        # Total number of constraints: (number of cells) x [
        #   (number of cells in rows - 1) +
        #   (number of cells in columns - 1) +
        #   (number of cells in region - 1 - cells used in row/column constraints)
        # ]
        # 9 * 9 * ((9 - 1) + (9 - 1) + (9 - 1 - 4)) = 1620
        # 4 * 4 * ((4 - 1) + (4 - 1) + (4 - 1 - 2)) = 112
        expected_num_constraints = 1620
        if size == 4:
            expected_num_constraints = 112
        actual_num_constraints = 0
        for i in csp.constraints.keys():
            actual_num_constraints += len(csp.constraints[i])
        self.assertEqual(expected_num_constraints, actual_num_constraints)

    def test_generate_csp_with_blank_board(self):
        self.assert_correct_CSP(values=None)

    def test_generate_csp_with_blank_4x4_board(self):
        self.assert_correct_CSP(values=None, size=4)

    def test_generate_csp_with_some_values_filled(self):
        # First row is filled 1-9, while the rest are blank
        size = 9
        values = [i for i in range(1, size+1)]
        for i in range(size-1):
            values.extend([0 for i in range(size)])
        self.assert_correct_CSP(values, size)

    def test_generate_csp_with_some_4x4_values_filled(self):
        # First row is filled 1-4, while the rest are blank
        size = 4
        values = [i for i in range(1, size+1)]
        for i in range(size-1):
            values.extend([0 for i in range(size)])
        self.assert_correct_CSP(values, size)

    def test_generate_csp_with_all_values_filled(self):
        # Sudoku solution taken from https://en.wikipedia.org/wiki/Sudoku
        values = [
            5, 3, 4, 6, 7, 8, 9, 1, 2,
            6, 7, 2, 1, 9, 5, 3, 4, 8,
            1, 9, 8, 3, 4, 2, 5, 6, 7,
            8, 5, 9, 7, 6, 1, 4, 2, 3,
            4, 2, 6, 8, 5, 3, 7, 9, 1,
            7, 1, 3, 9, 2, 4, 8, 5, 6,
            9, 6, 1, 5, 3, 7, 2, 8, 4,
            2, 8, 7, 4, 1, 9, 6, 3, 5,
            3, 4, 5, 2, 8, 6, 1, 7, 9
        ]
        self.assert_correct_CSP(values)

    def test_generate_csp_with_all_4x4_values_filled(self):
        values = [
            1, 2, 3, 4,
            3, 4, 1, 2,
            2, 3, 4, 1,
            4, 1, 2, 3
        ]
        self.assert_correct_CSP(values, size=4)


if __name__ == '__main__':
    unittest.main()
