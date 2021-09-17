import math
from collections import deque
from enum import Enum, IntEnum, auto
import copy


class AlgorithmTypes(IntEnum):
    AC3 = auto()
    BACKTRACKING_SEARCH = auto()


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

    def get_variables(self):
        return self.variables

    def get_neighbors(self, variable):
        return self.neighbors[variable]

    def get_domain(self, variable):
        return self.domains[variable]

    def get_all_domains(self):
        return self.domains

    def get_constraints(self, first_var, second_var):
        return self.constraints[first_var][second_var]

    def delete_from_domain(self, variable, value):
        self.domains[variable].remove(value)


class AC3HistoryItems(Enum):
    CURRENT_ARC = auto()
    CURRENT_QUEUE = auto()
    DOMAINS = auto()
    MESSAGE = auto()


class AC3:
    def __init__(self, csp: ConstraintSatisfactionProblem, record_history=False):
        self.csp = csp
        self.solution = None
        self.is_consistent = False
        self.record_history = record_history
        self.history = []

    def run(self):
        self.is_consistent = self.run_algorithm()
        if self.is_consistent:
            self.solution = {}
            for variable in self.csp.get_variables():
                # This can return multiple values for a variable if there are multiple solutions.
                self.solution[variable] = self.csp.get_domain(variable)
        return self.solution

    # Based on AC-3 pseudo-code from AIMA 3rd ed. Chapter 6
    def run_algorithm(self) -> bool:
        # Add all variable pairs as arcs. Arcs A->B and B->A should both be added so that the values in A and B can be
        # tested against each other.
        queue = []
        for first_var in self.csp.get_variables():
            for second_var in self.csp.get_neighbors(first_var):
                queue.append((first_var, second_var))
        if self.record_history:
            history_item = {
                AC3HistoryItems.CURRENT_ARC: (),
                AC3HistoryItems.CURRENT_QUEUE: list(queue),
                # Need to do a deep copy to preserve state of this variable
                AC3HistoryItems.DOMAINS: copy.deepcopy(self.csp.get_all_domains()),
                AC3HistoryItems.MESSAGE: "Initialized queue and domains."
            }
            self.history.append(history_item)
        # Turn the list into a FIFO queue
        queue = deque(queue)
        while len(queue) > 0:
            history_item = {}
            first_var, second_var = queue.popleft()
            if self.record_history:
                history_item = {
                    AC3HistoryItems.CURRENT_ARC: (first_var, second_var),
                    AC3HistoryItems.CURRENT_QUEUE: list(queue),
                    AC3HistoryItems.DOMAINS: copy.deepcopy(self.csp.get_all_domains()),
                    AC3HistoryItems.MESSAGE: "Popped arc from queue."
                }
                self.history.append(history_item)
            if self.revise(first_var, second_var):
                if self.record_history:
                    history_item = {
                        AC3HistoryItems.CURRENT_ARC: (first_var, second_var),
                        AC3HistoryItems.DOMAINS: copy.deepcopy(self.csp.get_all_domains())
                    }
                if len(self.csp.get_domain(first_var)) == 0:
                    if self.record_history:
                        history_item[AC3HistoryItems.CURRENT_QUEUE] = list(queue)
                        history_item[AC3HistoryItems.MESSAGE] = "Domain for variable '" + str(first_var) + \
                                                                "' is empty. No consistent assignment found."
                        self.history.append(history_item)
                    return False
                for neighbor in self.csp.get_neighbors(first_var):
                    if neighbor != second_var:
                        queue.append((neighbor, first_var))
                if self.record_history:
                    history_item[AC3HistoryItems.CURRENT_QUEUE] = list(queue)
                    history_item[AC3HistoryItems.MESSAGE] = "Updated domains and queue."
                    self.history.append(history_item)
        # Update the message of the last step to include the fact that the algorithm has stopped.
        self.history[-1][AC3HistoryItems.MESSAGE] += " Search has completed."
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


class SelectUnassignedVariableHeuristics(Enum):
    none = auto()
    MRV = auto()
    DegreeHeuristic = auto()


class OrderDomainValuesHeuristics(Enum):
    none = auto()
    LCV = auto()


class InferenceFunctions(Enum):
    none = auto()
    ForwardChecking = auto()


class BacktrackingSearchHistoryItems(Enum):
    CURRENT_VARIABLE = auto()
    ORDERED_VALUES = auto()
    CURRENT_VALUE = auto()
    INFERENCES = auto()
    CURRENT_ASSIGNMENT = auto()
    MESSAGE = auto()


class BacktrackingSearch:
    def __init__(
            self,
            csp: ConstraintSatisfactionProblem,
            select_unassigned_variable_heuristic=SelectUnassignedVariableHeuristics.none,
            order_domain_values_heuristic=OrderDomainValuesHeuristics.none,
            inference_function=InferenceFunctions.none,
            record_history=False
    ):
        self.csp = csp
        self.select_unassigned_variable_heuristic = None
        self.order_domain_values_heuristic = None
        self.inference_function = None
        if select_unassigned_variable_heuristic in SelectUnassignedVariableHeuristics:
            self.select_unassigned_variable_heuristic = select_unassigned_variable_heuristic
        else:
            raise ValueError("Invalid value for select_unassigned_variable_heuristic")
        if order_domain_values_heuristic in OrderDomainValuesHeuristics:
            self.order_domain_values_heuristic = order_domain_values_heuristic
        else:
            raise ValueError("Invalid value for order_domain_values_heuristic")
        if inference_function in InferenceFunctions:
            self.inference_function = inference_function
        else:
            raise ValueError("Invalid value for inference_function")
        if select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.MRV and \
                inference_function == InferenceFunctions.none:
            raise ValueError("Using the MRV heuristic requires an inference function")
        self.solution = None
        self.record_history = record_history
        self.history = []

    def run(self):
        self.solution = self.run_algorithm()
        return self.solution

    # Based on Backtracking-Search pseudo-code from AIMA 3rd ed. Chapter 6
    def run_algorithm(self):
        return self.backtrack({}, None)

    def backtrack(self, assignment: dict, inferences):
        if self.complete_assignment(assignment):
            if self.record_history:
                history_item = self.create_history_item(
                    assignment=assignment,
                    inferences=inferences,
                    message="Assignment is complete."
                )
                self.history.append(history_item)
            return assignment
        variable = self.select_unassigned_variable(assignment, inferences)
        ordered_values = self.order_domain_values(variable, assignment, inferences)
        for value in ordered_values:
            if self.record_history:
                history_item = self.create_history_item(
                    assignment=assignment,
                    inferences=inferences,
                    current_variable=variable,
                    current_value=value,
                    ordered_values=ordered_values,
                    message="Selected variable and value."
                )
                self.history.append(history_item)
            if self.is_consistent(variable, value, assignment):
                assignment[variable] = value
                new_inferences = self.inference(variable, value, self.inference_function, inferences)
                if self.record_history:
                    history_item = self.create_history_item(
                        assignment=assignment,
                        inferences=new_inferences,
                        current_variable=variable,
                        current_value=value,
                        ordered_values=ordered_values,
                        message="Updated assignment and inferences."
                    )
                    self.history.append(history_item)
                # Only continue if there are valid inferences. Otherwise, it means there will be a variable with no
                # valid assignment.
                new_inferences_valid = self.all_domains_have_values(new_inferences)
                if new_inferences_valid:
                    result = self.backtrack(assignment, new_inferences)
                    if result:
                        return result
            else:
                if self.record_history:
                    history_item = self.create_history_item(
                        assignment=assignment,
                        inferences=inferences,
                        current_variable=variable,
                        current_value=value,
                        ordered_values=ordered_values,
                        message="Value is not consistent with assignment."
                    )
                    self.history.append(history_item)
        # Need to remove variable assignment as the assignment variable is mutable, so it is passed by reference.
        if variable in assignment.keys():
            del assignment[variable]
        if self.record_history:
            message = "No values in remaining variables satisfy current assignment."
            if len(assignment) == 0:
                # If we've backtracked all the way to the beginning, there is no consistent assignment.
                message += " No consistent assignment found."
            else:
                message += " Backtracking..."
            history_item = self.create_history_item(
                assignment=assignment,
                inferences=inferences,
                current_variable=variable,
                ordered_values=ordered_values,
                message=message
            )
            self.history.append(history_item)
        return None

    @staticmethod
    def create_history_item(
            current_variable: str = None,
            ordered_values: list = None,
            current_value = None,
            inferences = None,
            assignment: dict = None,
            message: str = None
    ) -> dict:
        history_item = {
            BacktrackingSearchHistoryItems.CURRENT_VARIABLE: current_variable,
            BacktrackingSearchHistoryItems.ORDERED_VALUES: copy.copy(ordered_values),
            BacktrackingSearchHistoryItems.CURRENT_VALUE: current_value,
            # Dictionaries need to be deep copies to store the current state
            BacktrackingSearchHistoryItems.INFERENCES: copy.deepcopy(inferences),
            BacktrackingSearchHistoryItems.CURRENT_ASSIGNMENT: copy.deepcopy(assignment),
            BacktrackingSearchHistoryItems.MESSAGE: message
        }
        return history_item

    def complete_assignment(self, assignment: dict) -> bool:
        for variable in self.csp.get_variables():
            if variable not in assignment.keys():
                return False
            if not assignment[variable]:
                return False
        return True

    def select_unassigned_variable(self, assignment: dict, inferences):
        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.MRV or\
                self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DegreeHeuristic:
            # Minimum-remaining-values heuristic
            # Select the variable with the fewest number of possible values
            if not inferences:
                # Usually there will have been inferencing done to minimize the domain values, but at the beginning, use
                # the whole domain.
                inferences = self.csp.get_all_domains()
            minimum_remaining_values = math.inf
            maximum_num_constraints = 0
            chosen_variable = None
            for variable in self.csp.get_variables():
                if variable not in assignment.keys():
                    if len(inferences[variable]) < minimum_remaining_values:
                        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DegreeHeuristic:
                            maximum_num_constraints = self.get_num_constraints_with_unassigned_neighbors(assignment, variable)
                        minimum_remaining_values = len(inferences[variable])
                        chosen_variable = variable
                    elif len(inferences[variable]) == minimum_remaining_values:
                        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DegreeHeuristic:
                            # Degree heuristic
                            # Select variable with largest number of constraints on other unassigned variables as
                            # tie-breaker for MRV.
                            num_constraints = self.get_num_constraints_with_unassigned_neighbors(assignment, variable)
                            if num_constraints > maximum_num_constraints:
                                maximum_num_constraints = num_constraints
                                minimum_remaining_values = len(inferences[variable])
                                chosen_variable = variable
            return chosen_variable
        else:
            # Naively select "next" variable
            for variable in self.csp.get_variables():
                if variable not in assignment.keys():
                    return variable

    def get_num_constraints_with_unassigned_neighbors(self, assignment: dict, variable):
        maximum_num_constraints = 0
        for neighbor in self.csp.get_neighbors(variable):
            if neighbor not in assignment.keys():
                maximum_num_constraints += len(self.csp.get_constraints(variable, neighbor))
        return maximum_num_constraints

    def order_domain_values(self, variable, assignment: dict, inferences):
        if self.order_domain_values_heuristic == OrderDomainValuesHeuristics.LCV:
            # Least-constraining-value heuristic
            # Prefer value that rules out the fewest choices for neighbors
            ordered_values_temp = []
            for value in self.csp.get_domain(variable):
                domains = self.inference(variable, value, InferenceFunctions.ForwardChecking, inferences)
                total_num_values = 0
                for neighbor in self.csp.get_neighbors(variable):
                    total_num_values += len(domains[neighbor])
                ordered_values_temp.append([value, total_num_values])
            # Sort by total number of values in neighbors descending
            ordered_values = sorted(ordered_values_temp, key=lambda x: x[1], reverse=True)
            ordered_values = [value[0] for value in ordered_values]
            return ordered_values
        else:
            # Naively select "next" value
            if inferences:
                return inferences[variable]
            else:
                return self.csp.get_domain(variable)

    def is_consistent(self, variable, value, assignment):
        # Check if the value violates any of the constraints with already-assigned neighbors
        for neighbor in self.csp.get_neighbors(variable):
            if neighbor in assignment.keys():
                for constraint_func in self.csp.get_constraints(variable, neighbor):
                    if not constraint_func(value, assignment[neighbor]):
                        return False
        return True

    # Allow passing in the inference function instead of checking class variable so that this can be re-used
    def inference(self, variable, value, inference_function=None, inferences=None):
        if inference_function == InferenceFunctions.ForwardChecking:
            # Create a new copy where any values in neighbors' domains that violate constraints are removed.
            if inferences:
                # If we've already done inferencing, use the existing inferences
                old_domains = inferences
            else:
                # Otherwise, use the domains of the variables
                old_domains = self.csp.get_all_domains()
            new_domains = copy.deepcopy(old_domains)
            for neighbor in self.csp.get_neighbors(variable):
                for constraint_func in self.csp.get_constraints(variable, neighbor):
                    # Reference old_domains so we're not modifying a collection in-place
                    for neighbor_value in old_domains[neighbor]:
                        if not constraint_func(value, neighbor_value):
                            new_domains[neighbor].remove(neighbor_value)
            # Also remove all other values from variable's domain
            for old_value in old_domains[variable]:
                if old_value != value:
                    new_domains[variable].remove(old_value)
            return new_domains
        else:
            # Naively return the domains of all variables (i.e. everything is valid)
            return self.csp.get_all_domains()

    @staticmethod
    def all_domains_have_values(domains: dict) -> bool:
        for variable_name in domains.keys():
            if len(domains[variable_name]) == 0:
                return False
        return True
