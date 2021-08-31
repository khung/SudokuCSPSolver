import unittest
from algorithms import *
from sudoku_board import *


class TestAlgorithms(unittest.TestCase):
    # Sudoku solution taken from https://en.wikipedia.org/wiki/Sudoku
    sudoku_puzzle_solvable = [
        5, 3, 0, 0, 7, 0, 0, 0, 0,
        6, 0, 0, 1, 9, 5, 0, 0, 0,
        0, 9, 8, 0, 0, 0, 0, 6, 0,
        8, 0, 0, 0, 6, 0, 0, 0, 3,
        4, 0, 0, 8, 0, 3, 0, 0, 1,
        7, 0, 0, 0, 2, 0, 0, 0, 6,
        0, 6, 0, 0, 0, 0, 2, 8, 0,
        0, 0, 0, 4, 1, 9, 0, 0, 5,
        0, 0, 0, 0, 8, 0, 0, 7, 9
    ]
    sudoku_solution_solvable = [
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
    # Leave only 16 clues to create a Sudoku puzzle with multiple solutions. Verified using solution count on
    # https://www.sudokuwiki.org/sudoku.htm.
    # Reference:
    # Gary McGuire, Bastian Tugemann & Gilles Civario (2014) There Is No 16-Clue Sudoku: Solving the Sudoku Minimum
    # Number of Clues Problem via Hitting Set Enumeration, Experimental Mathematics, 23:2, 190-217,
    # DOI: 10.1080/10586458.2013.870056
    sudoku_puzzle_multiple_solutions = [
        5, 0, 0, 0, 7, 0, 0, 0, 0,
        6, 0, 0, 1, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 6, 0,
        8, 0, 0, 0, 6, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 1,
        0, 0, 0, 0, 2, 0, 0, 0, 6,
        0, 6, 0, 0, 0, 0, 2, 0, 0,
        0, 0, 0, 4, 0, 0, 0, 0, 5,
        0, 0, 0, 0, 0, 0, 0, 7, 9
    ]
    # Incorrectly set a value to a cell so the Sudoku no longer has any solution. Verified using solution count on
    # https://www.sudokuwiki.org/sudoku.htm.
    sudoku_puzzle_no_solution = [
        5, 3, 0, 0, 7, 0, 0, 0, 0,
        6, 0, 0, 1, 9, 5, 0, 0, 0,
        0, 9, 8, 0, 0, 0, 0, 6, 0,
        8, 0, 0, 0, 6, 0, 0, 0, 3,
        4, 0, 0, 8, 0, 3, 0, 0, 1,
        1, 0, 0, 0, 2, 0, 0, 0, 6,  # 7 replaced by 1
        0, 6, 0, 0, 0, 0, 2, 8, 0,
        0, 0, 0, 4, 1, 9, 0, 0, 5,
        0, 0, 0, 0, 8, 0, 0, 7, 9
    ]
    # 4x4 board to test inefficient heuristics
    sudoku_puzzle_4x4_solvable = [
        0, 2, 0, 4,
        3, 0, 1, 0,
        0, 3, 0, 1,
        4, 0, 2, 0
    ]
    sudoku_solution_4x4_solvable = [
        1, 2, 3, 4,
        3, 4, 1, 2,
        2, 3, 4, 1,
        4, 1, 2, 3
    ]

    def test_ac3_on_trivial_csp(self):
        def not_equal(v1, v2):
            return v1 != v2
        variables = ["11", "12", "21", "22"]
        domains = [[1, 2, 3, 4], [2], [3], [4]]
        constraints = []
        for i in range(len(variables)):
            for j in range(i+1, len(variables)):
                if i != j:
                    constraints.append((variables[i], variables[j], not_equal))
        solution = {"11": [1], "12": [2], "21": [3], "22": [4]}
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        self.assertDictEqual(solution, result)

    def test_ac3_on_solvable_sudoku(self):
        solution_dict = {}
        for i in range(9):
            for j in range(9):
                var_name = str((i+1)*10 + (j+1))
                solution_dict[var_name] = [self.sudoku_solution_solvable[i*9 + j]]
        board = SudokuBoard(initial_values=self.sudoku_puzzle_solvable)
        csp = board.generate_csp()
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        self.assertDictEqual(solution_dict, result)

    def test_ac3_on_unsolvable_sudoku_1(self):
        # Check that multiple solutions are returned
        board = SudokuBoard(initial_values=self.sudoku_puzzle_multiple_solutions)
        csp = board.generate_csp()
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        multiple_solutions = False
        for variable in result.keys():
            if len(result[variable]) > 1:
                multiple_solutions = True
                break
        self.assertTrue(multiple_solutions)

    def test_ac3_on_unsolvable_sudoku_2(self):
        board = SudokuBoard(initial_values=self.sudoku_puzzle_no_solution)
        csp = board.generate_csp()
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        self.assertIsNone(result)

    def test_ac3_on_solvable_4x4_sudoku(self):
        sudoku_size = 4
        solution_dict = {}
        for i in range(sudoku_size):
            for j in range(sudoku_size):
                var_name = str((i+1)*10 + (j+1))
                solution_dict[var_name] = [self.sudoku_solution_4x4_solvable[i*sudoku_size + j]]
        board = SudokuBoard(initial_values=self.sudoku_puzzle_4x4_solvable, size=sudoku_size)
        csp = board.generate_csp()
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        self.assertDictEqual(solution_dict, result)

    def test_backtracking_on_trivial_csp(self):
        def not_equal(v1, v2):
            return v1 != v2
        variables = ["11", "12", "21", "22"]
        domains = [[1, 2, 3, 4], [2], [3], [4]]
        constraints = []
        for i in range(len(variables)):
            for j in range(i+1, len(variables)):
                if i != j:
                    constraints.append((variables[i], variables[j], not_equal))
        solution = {"11": 1, "12": 2, "21": 3, "22": 4}
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        backtracking_runner = BacktrackingSearch(csp)
        result = backtracking_runner.run()
        self.assertDictEqual(solution, result)

    def test_backtracking_on_solvable_sudoku(self):
        sudoku_size = 4
        solution_dict = {}
        for i in range(sudoku_size):
            for j in range(sudoku_size):
                var_name = str((i+1)*10 + (j+1))
                solution_dict[var_name] = self.sudoku_solution_4x4_solvable[i*sudoku_size + j]
        board = SudokuBoard(initial_values=self.sudoku_puzzle_4x4_solvable, size=sudoku_size)
        csp = board.generate_csp()
        backtracking_runner = BacktrackingSearch(csp)
        result = backtracking_runner.run()
        self.assertDictEqual(solution_dict, result)

    def test_backtracking_with_forward_checking(self):
        sudoku_size = 4
        solution_dict = {}
        for i in range(sudoku_size):
            for j in range(sudoku_size):
                var_name = str((i+1)*10 + (j+1))
                solution_dict[var_name] = self.sudoku_solution_4x4_solvable[i*sudoku_size + j]
        board = SudokuBoard(initial_values=self.sudoku_puzzle_4x4_solvable, size=sudoku_size)
        csp = board.generate_csp()
        backtracking_runner = BacktrackingSearch(csp, inference_function=InferenceFunctions.ForwardChecking)
        result = backtracking_runner.run()
        self.assertDictEqual(solution_dict, result)

    def test_backtracking_with_LCV(self):
        sudoku_size = 4
        solution_dict = {}
        for i in range(sudoku_size):
            for j in range(sudoku_size):
                var_name = str((i + 1) * 10 + (j + 1))
                solution_dict[var_name] = self.sudoku_solution_4x4_solvable[i * sudoku_size + j]
        board = SudokuBoard(initial_values=self.sudoku_puzzle_4x4_solvable, size=sudoku_size)
        csp = board.generate_csp()
        backtracking_runner = BacktrackingSearch(csp, order_domain_values_heuristic=OrderDomainValuesHeuristics.LCV)
        result = backtracking_runner.run()
        self.assertDictEqual(solution_dict, result)


if __name__ == '__main__':
    unittest.main()
