# Define what a constraint satisfaction problem should consist of
class ConstraintSatisfactionProblem:
    def __init__(self, variables: list, domains: list, constraints: list):
        if len(variables) != len(domains):
            raise ValueError("Number of domains must match number of variables")
        self.variables = variables
        self.domains = {}
        for i in range(len(variables)):
            self.domains[variables[i]] = domains[i]
        # Create dictionary of dictionaries for fast constraint lookup
        # Assumes constraints are in the form (variable 1, variable 2, constraint function) where the constraint
        # function returns true if constraint is satisfied.
        self.constraints = {}
        for first_var, second_var, constraint_func in constraints:
            # AC-3 seems to assume symmetric constraints, so we add both ways
            constraints_to_add = [
                (first_var, second_var, constraint_func),
                (second_var, first_var, constraint_func)
            ]
            for constraint in constraints_to_add:
                # Okay to shadow as we don't use the original values anymore
                first_var, second_var, constraint_func = constraint
                if first_var not in self.constraints.keys():
                    self.constraints[first_var] = {}
                if second_var not in self.constraints[first_var].keys():
                    self.constraints[first_var][second_var] = [constraint_func]
                elif constraint_func not in self.constraints[first_var][second_var]:
                    # Only add constraint if it's not already there due to a prior symmetric constraint
                    self.constraints[first_var][second_var].append(constraint_func)
        # Bookkeeping variables
        self.neighbors = {}
        for key in self.constraints.keys():
            self.neighbors[key] = self.constraints[key].keys()

    def get_neighbors(self, variable):
        return self.neighbors[variable]

    def get_domain(self, variable):
        return self.domains[variable]

    def get_constraints(self, first_var, second_var):
        return self.constraints[first_var][second_var]

    def delete_from_domain(self, variable, value):
        self.domains[variable].remove(value)


class AC3:
    def __init__(self, csp: ConstraintSatisfactionProblem):
        self.csp = csp
        self.solution = None
        self.is_consistent = False

    def run(self):
        self.is_consistent = self.run_algorithm()
        if self.is_consistent:
            self.solution = {}
            for variable in self.csp.variables:
                domain = self.csp.get_domain(variable)
                assert len(domain) == 1
                self.solution[variable] = domain[0]
        return self.solution

    # Based on AC-3 pseudo-code from AIMA 3rd ed. Chapter 6
    def run_algorithm(self) -> bool:
        queue = []
        for first_var in self.csp.variables:
            for second_var in self.csp.get_neighbors(first_var):
                # Assumes that the variables can be sorted in some stable order
                arc = tuple(sorted([first_var, second_var]))
                if arc not in queue:
                    queue.append(arc)
        while len(queue) > 0:
            first_var, second_var = queue.pop()
            if self.revise(first_var, second_var):
                if len(self.csp.get_domain(first_var)) == 0:
                    return False
                for neighbor in self.csp.get_neighbors(first_var):
                    if neighbor != second_var:
                        queue.append((neighbor, first_var))
        return True

    def revise(self, first_var, second_var) -> bool:
        revised = False
        for first_var_value in self.csp.get_domain(first_var):
            constraints_satisfiable = False
            for second_var_value in self.csp.get_domain(second_var):
                for constraint_func in self.csp.get_constraints(first_var, second_var):
                    if constraint_func(first_var_value, second_var_value):
                        constraints_satisfiable = True
                if constraints_satisfiable:
                    break
            if not constraints_satisfiable:
                self.csp.delete_from_domain(first_var, first_var_value)
                revised = True
        return revised
