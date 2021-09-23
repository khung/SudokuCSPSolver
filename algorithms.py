import collections
import math
from collections import deque
from enum import Enum, IntEnum, auto
import copy
from typing import Optional, Any


class AlgorithmTypes(IntEnum):
    """CSP algorithm types."""
    AC3 = auto()
    BACKTRACKING_SEARCH = auto()


class ConstraintSatisfactionProblem:
    """
    Defines what a constraint satisfaction problem (CSP) should consist of so that a CSP algorithm can use it.

    Public methods
    --------------
    * get_neighbors
    * get_domain
    * get_all_domains
    * get_constraints
    * delete_from_domain

    Instance variables
    ------------------
    * variables
    """

    def __init__(self, variables: list, domains: list, constraints: list) -> None:
        """
        :param variables: A list of variables in the CSP, where the variable is any hashable type (usually a string).
        :param domains: A list of domains for each variable, in the same order as variables.
        :param constraints: A list of constraints in the form (variable_1, variable_2, constraint_function) where
        the constraint function returns true if the constraint is satisfied.
        """
        if len(variables) != len(domains):
            raise ValueError("Number of domains must match number of variables")
        self.variables = variables
        self._domains = {}
        for i in range(len(variables)):
            self._domains[variables[i]] = domains[i]
        # Create dictionary of dictionaries for fast constraint lookup
        self._constraints = {}
        for first_var, second_var, constraint_func in constraints:
            # AC-3 seems to assume symmetric constraints, so we add both ways
            constraints_to_add = [
                (first_var, second_var, constraint_func),
                (second_var, first_var, constraint_func)
            ]
            for constraint in constraints_to_add:
                # Okay to shadow as we don't use the original values anymore
                first_var, second_var, constraint_func = constraint
                if first_var not in self._constraints.keys():
                    self._constraints[first_var] = {}
                if second_var not in self._constraints[first_var].keys():
                    self._constraints[first_var][second_var] = [constraint_func]
                elif constraint_func not in self._constraints[first_var][second_var]:
                    # Only add constraint if it's not already there due to a prior symmetric constraint
                    self._constraints[first_var][second_var].append(constraint_func)
        # Bookkeeping variables
        self._neighbors = {}
        for key in self._constraints.keys():
            self._neighbors[key] = self._constraints[key].keys()

    def get_neighbors(self, variable) -> collections.KeysView:
        """
        Get all the neighbors of a variable.

        :param variable: A hashable object (usually a string) used to look up the variable's neighbors.
        :return: The neighbors of that variable.
        """
        return self._neighbors[variable]

    def get_domain(self, variable) -> list:
        """
        Get the domain (possible values) of a variable.

        :param variable: A hashable object (usually a string) used to look up the variable's domain.
        :return: The domain of that variable.
        """
        return self._domains[variable]

    def get_all_domains(self) -> dict:
        """
        Get all domains in this CSP.

        :return: A dictionary of all domains.
        """
        return self._domains

    def get_constraints(self, first_var, second_var) -> list:
        """
        Get all constraints between two variables.

        :param first_var: A hashable object (usually a string) representing the first variable.
        :param second_var: A hashable object (usually a string) representing the second variable.
        :return: All constraints between the two variables.
        """
        return self._constraints[first_var][second_var]

    def delete_from_domain(self, variable, value) -> None:
        """
        Delete a value from a domain.

        :param variable: A hashable object (usually a string) representing a variable.
        :param value: The value to delete from the domain.
        """
        self._domains[variable].remove(value)


class AC3HistoryItems(Enum):
    """Possible items that can be stored in a step in the history of a run of the AC-3 algorithm."""
    CURRENT_ARC = auto()
    CURRENT_QUEUE = auto()
    DOMAINS = auto()
    MESSAGE = auto()


class AC3:
    """
    Class for running the AC-3 algorithm.

    Public methods
    --------------
    * run

    Instance variables
    ------------------
    * csp
    * solution
    * is_consistent
    * record_history
    * history
    """

    def __init__(self, csp: ConstraintSatisfactionProblem, record_history: bool = False) -> None:
        """
        :param csp: A CSP containing the problem to solve.
        :param record_history: Whether to record the history of a run.
        """
        self.csp = csp
        self.solution = None
        self.is_consistent = False
        self.record_history = record_history
        self.history = []

    def run(self) -> Optional[dict]:
        """
        The main entry point for running the AC-3 algorithm.

        :return: A dictionary of the remaining domains of each variable after the run. If no consistent assignment can
        be found (i.e. the domain of a variable became empty), None is returned.
        """
        self.is_consistent = self._run_algorithm()
        if self.is_consistent:
            self.solution = {}
            for variable in self.csp.variables:
                # This can return multiple values for a variable if there are multiple solutions.
                self.solution[variable] = self.csp.get_domain(variable)
        return self.solution

    def _run_algorithm(self) -> bool:
        """The implementation of the AC-3 algorithm. Based on AC-3 pseudo-code from AIMA 3rd ed. Chapter 6."""
        # Add all variable pairs as arcs. Arcs A->B and B->A should both be added so that the values in A and B can be
        # tested against each other.
        queue = []
        for first_var in self.csp.variables:
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
            if self._revise(first_var, second_var):
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
        if self.record_history:
            self.history[-1][AC3HistoryItems.MESSAGE] += " Search has completed."
        return True

    def _revise(self, first_var, second_var) -> bool:
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
    """All implemented Select-Unassigned-Variable heuristics."""
    none = auto()
    MRV = auto()
    DEGREE_HEURISTIC = auto()


class OrderDomainValuesHeuristics(Enum):
    """All implemented Order-Domain-Values heuristics."""
    none = auto()
    LCV = auto()


class InferenceFunctions(Enum):
    """All implemented inference functions."""
    none = auto()
    FORWARD_CHECKING = auto()


class BacktrackingSearchHistoryItems(Enum):
    """Possible items that can be stored in a step in the history of a run of the backtracking search algorithm."""
    CURRENT_VARIABLE = auto()
    ORDERED_VALUES = auto()
    CURRENT_VALUE = auto()
    INFERENCES = auto()
    CURRENT_ASSIGNMENT = auto()
    MESSAGE = auto()


class BacktrackingSearch:
    """
    Class for running the backtracking search algorithm.

    Public methods
    --------------
    * run

    Instance variables
    ------------------
    * csp
    * select_unassigned_variable_heuristic
    * order_domain_values_heuristic
    * inference_function
    * solution
    * record_history
    * history
    """
    def __init__(
            self,
            csp: ConstraintSatisfactionProblem,
            select_unassigned_variable_heuristic: SelectUnassignedVariableHeuristics
            = SelectUnassignedVariableHeuristics.none,
            order_domain_values_heuristic: OrderDomainValuesHeuristics = OrderDomainValuesHeuristics.none,
            inference_function: InferenceFunctions = InferenceFunctions.none,
            record_history: bool = False
    ) -> None:
        """
        :param csp: A CSP containing the problem to solve.
        :param select_unassigned_variable_heuristic: The Select-Unassigned-Variable heuristic to use.
        :param order_domain_values_heuristic: The Order-Domain-Values heuristic to use.
        :param inference_function: The inference function to use.
        :param record_history: Whether to record the history of a run.
        """
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

    def run(self) -> Optional[dict]:
        """
        The main entry point for running the backtracking search algorithm.

        :return: A dictionary of the complete assignment after the run. If no complete assignment can be found, None
        is returned.
        """
        self.solution = self._run_algorithm()
        return self.solution

    def _run_algorithm(self) -> Optional[dict]:
        """The implementation of the backtracking search algorithm. Based on Backtracking-Search pseudo-code from AIMA
        3rd ed. Chapter 6."""
        return self._backtrack({}, None)

    def _backtrack(self, assignment: dict, inferences: Optional[dict]) -> Optional[dict]:
        if self._complete_assignment(assignment):
            if self.record_history:
                history_item = self._create_history_item(
                    assignment=assignment,
                    inferences=inferences,
                    message="Assignment is complete."
                )
                self.history.append(history_item)
            return assignment
        variable = self._select_unassigned_variable(assignment, inferences)
        ordered_values = self._order_domain_values(variable, inferences)
        for value in ordered_values:
            if self.record_history:
                history_item = self._create_history_item(
                    assignment=assignment,
                    inferences=inferences,
                    current_variable=variable,
                    current_value=value,
                    ordered_values=ordered_values,
                    message="Selected variable and value."
                )
                self.history.append(history_item)
            if self._is_consistent(variable, value, assignment):
                assignment[variable] = value
                new_inferences = self._inference(variable, value, self.inference_function, inferences)
                if self.record_history:
                    history_item = self._create_history_item(
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
                new_inferences_valid = self._all_domains_have_values(new_inferences)
                if new_inferences_valid:
                    result = self._backtrack(assignment, new_inferences)
                    if result:
                        return result
            else:
                if self.record_history:
                    history_item = self._create_history_item(
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
            history_item = self._create_history_item(
                assignment=assignment,
                inferences=inferences,
                current_variable=variable,
                ordered_values=ordered_values,
                message=message
            )
            self.history.append(history_item)
        return None

    @staticmethod
    def _create_history_item(
            current_variable: Optional[str] = None,
            ordered_values: Optional[list] = None,
            current_value=None,
            inferences: Optional[dict] = None,
            assignment: Optional[dict] = None,
            message: Optional[str] = None
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

    def _complete_assignment(self, assignment: dict) -> bool:
        for variable in self.csp.variables:
            if variable not in assignment.keys():
                return False
            if not assignment[variable]:
                return False
        return True

    def _select_unassigned_variable(self, assignment: dict, inferences: Optional[dict]) -> Any:
        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.MRV or\
                self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DEGREE_HEURISTIC:
            # Minimum-remaining-values heuristic
            # Select the variable with the fewest number of possible values
            if not inferences:
                # Usually there will have been inferencing done to minimize the domain values, but at the beginning, use
                # the whole domain.
                inferences = self.csp.get_all_domains()
            minimum_remaining_values = math.inf
            maximum_num_constraints = 0
            chosen_variable = None
            for variable in self.csp.variables:
                if variable not in assignment.keys():
                    if len(inferences[variable]) < minimum_remaining_values:
                        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DEGREE_HEURISTIC:
                            maximum_num_constraints = self._get_num_constraints_with_unassigned_neighbors(assignment, variable)
                        minimum_remaining_values = len(inferences[variable])
                        chosen_variable = variable
                    elif len(inferences[variable]) == minimum_remaining_values:
                        if self.select_unassigned_variable_heuristic == SelectUnassignedVariableHeuristics.DEGREE_HEURISTIC:
                            # Degree heuristic
                            # Select variable with largest number of constraints on other unassigned variables as
                            # tie-breaker for MRV.
                            num_constraints = self._get_num_constraints_with_unassigned_neighbors(assignment, variable)
                            if num_constraints > maximum_num_constraints:
                                maximum_num_constraints = num_constraints
                                minimum_remaining_values = len(inferences[variable])
                                chosen_variable = variable
            return chosen_variable
        else:
            # Naively select "next" variable
            for variable in self.csp.variables:
                if variable not in assignment.keys():
                    return variable

    def _get_num_constraints_with_unassigned_neighbors(self, assignment: dict, variable) -> int:
        maximum_num_constraints = 0
        for neighbor in self.csp.get_neighbors(variable):
            if neighbor not in assignment.keys():
                maximum_num_constraints += len(self.csp.get_constraints(variable, neighbor))
        return maximum_num_constraints

    def _order_domain_values(self, variable, inferences: Optional[dict]) -> list:
        if self.order_domain_values_heuristic == OrderDomainValuesHeuristics.LCV:
            # Least-constraining-value heuristic
            # Prefer value that rules out the fewest choices for neighbors
            ordered_values_temp = []
            if inferences:
                values_to_check = inferences[variable]
            else:
                values_to_check = self.csp.get_domain(variable)
            for value in values_to_check:
                domains = self._inference(variable, value, InferenceFunctions.FORWARD_CHECKING, inferences)
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

    def _is_consistent(self, variable, value, assignment: dict) -> bool:
        # Check if the value violates any of the constraints with already-assigned neighbors
        for neighbor in self.csp.get_neighbors(variable):
            if neighbor in assignment.keys():
                for constraint_func in self.csp.get_constraints(variable, neighbor):
                    if not constraint_func(value, assignment[neighbor]):
                        return False
        return True

    def _inference(
            self,
            variable,
            value,
            inference_function: InferenceFunctions = InferenceFunctions.none,
            inferences: Optional[dict] = None
    ) -> dict:
        if inference_function == InferenceFunctions.FORWARD_CHECKING:
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
    def _all_domains_have_values(domains: dict) -> bool:
        for variable_name in domains.keys():
            if len(domains[variable_name]) == 0:
                return False
        return True
