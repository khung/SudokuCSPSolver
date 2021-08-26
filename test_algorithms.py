import unittest
from algorithms import *


class TestAlgorithms(unittest.TestCase):
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
        solution = {"11": 1, "12": 2, "21": 3, "22": 4}
        csp = ConstraintSatisfactionProblem(variables, domains, constraints)
        ac3_runner = AC3(csp)
        result = ac3_runner.run()
        self.assertDictEqual(result, solution)


if __name__ == '__main__':
    unittest.main()
