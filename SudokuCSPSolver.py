import _thread
from tkinter import *
from tkinter.scrolledtext import *
from tkinter.ttk import *
# Re-import tkinter's Label so we can use it even when it's overridden by ttk's import
from tkinter import Label as TkLabel
from idlelib.tooltip import Hovertip
from sudoku_board import SudokuBoard
from algorithms import AC3, BacktrackingSearch, AC3HistoryItems, AlgorithmTypes, SelectUnassignedVariableHeuristics, \
    OrderDomainValuesHeuristics, InferenceFunctions, BacktrackingSearchHistoryItems
from enum import Enum, auto
from typing import Union, Callable


class Cell(Entry):
    """Extends the Entry widget to provide a cell for the Sudoku board."""

    def __init__(self, max_digit: int, master=None) -> None:
        """
        :param max_digit: The maximum digit to accept as input [1, max_digit].
        :param master: The parent Tk container.
        """
        super().__init__(
            master,
            width=1,
            font="Helvetica 20",
            justify="center"
        )
        # Only allow 1 digit between 1-board_size in entry
        # Validation documentation under http://tcl.tk/man/tcl8.6/TkCmd/entry.htm#M16
        command = (self.register(self._on_validate), "%P")
        self.configure(validate="key", validatecommand=command)
        self._max_digit = max_digit

    def _on_validate(self, new_value: str) -> bool:
        """
        Validate that the input is a digit between 1 and the board size (4 or 9).

        :param new_value: The new value that was entered as input.
        :return: Whether the input is valid.
        """
        if new_value == "":
            return True
        try:
            value = int(new_value)
            if 0 < value <= self._max_digit:
                return True
            else:
                return False
        except ValueError:
            return False


class SolverCell(Frame):
    """
    Extends Frame container to draw each cell in the solving mode.

    Public methods
    --------------
    * update_domain
    * select_cell
    * unselect_cell
    * select_value
    * unselect_value
    """

    # Style names
    unselected_cell_frame = 'Cell.TFrame'
    selected_cell_frame = 'SelectedCell.TFrame'
    unselected_cell_label = 'Cell.TLabel'
    unselected_cell_highlighted_value_1_label = 'Cell_HighlightValue1.TLabel'
    unselected_cell_highlighted_value_2_label = 'Cell_HighlightValue2.TLabel'
    selected_cell_label = 'SelectedCell.TLabel'
    selected_cell_highlighted_value_1_label = 'SelectedCell_HighlightValue1.TLabel'
    selected_cell_highlighted_value_2_label = 'SelectedCell_HighlightValue2.TLabel'

    def __init__(self, max_digit: int, master=None, **kw) -> None:
        """
        :param max_digit: The maximum digit in the domain of the cell (variable).
        :param master: The parent Tk container.
        """
        super().__init__(master, **kw)
        # Backgrounds need to be set for both frame and label for full coverage.
        s = Style()
        default_bg_color = s.lookup(style=master.cget('style'), option='background')
        s.configure(self.unselected_cell_frame, background=default_bg_color)
        s.configure(self.selected_cell_frame, background='light yellow')
        # Multiple styles have to be defined, as only one can be applied at a time.
        s.configure(self.unselected_cell_label, background=default_bg_color, foreground='black')
        s.configure(self.unselected_cell_highlighted_value_1_label, background=default_bg_color, foreground='red')
        s.configure(self.unselected_cell_highlighted_value_2_label, background=default_bg_color, foreground='blue')
        s.configure(self.selected_cell_label, background='light yellow', foreground='black')
        s.configure(self.selected_cell_highlighted_value_1_label, background='light yellow', foreground='red')
        s.configure(self.selected_cell_highlighted_value_2_label, background='light yellow', foreground='blue')
        self._max_digit = max_digit
        self._domain = self._make_gui()
        # Flag to specify whether this cell is currently selected
        self._selected = False
        # Set to unselected by default
        self.unselect_cell()

    def _make_gui(self) -> list:
        domain = []
        digit = 1
        # Positioning is not ideal (horizontal spacing is a bit too narrow), but this seems to be the best Tk can do.
        if self._max_digit == 9:
            range_end = 3
            font = "Helvetica 7"
            x_padding = 2
        elif self._max_digit == 4:
            range_end = 2
            font = "Helvetica 13"
            x_padding = 2
        else:
            raise ValueError("self.max_digit has an invalid value")
        # Create an inner frame to center the grid
        inner_frame = Frame(self)
        inner_frame.pack(expand=YES)
        for row in range(range_end):
            for col in range(range_end):
                domain_value_label = Label(
                    inner_frame,
                    text=str(digit),
                    font=font,
                    style=self.unselected_cell_label,
                    width=1,
                    justify="center"
                )
                # Options needed for background to fill correctly
                domain_value_label.grid(row=row, column=col, ipadx=x_padding, sticky=NSEW)
                domain.append(domain_value_label)
                digit += 1
        for i in range(range_end):
            inner_frame.columnconfigure(i, weight=1)
            inner_frame.rowconfigure(i, weight=1)
        return domain

    def update_domain(self, new_domain: list) -> None:
        """
        Update the domains in the cell.

        :param new_domain: The list of new domain values.
        """
        for digit_index in range(self._max_digit):
            digit = digit_index+1
            if digit in new_domain:
                # Make sure that the digit is shown if it's in the new domain
                self._domain[digit_index].configure(text=str(digit))
            else:
                # Make sure that the digit is not shown if it's not in the new domain
                self._domain[digit_index].configure(text=" ")

    def select_cell(self) -> None:
        """Highlight this cell."""
        self._selected = True
        self.configure(style=self.selected_cell_frame)
        for value_label in self._domain:
            old_style = value_label.cget('style')
            if old_style == self.unselected_cell_label:
                new_style = self.selected_cell_label
            elif old_style == self.unselected_cell_highlighted_value_1_label:
                new_style = self.selected_cell_highlighted_value_1_label
            elif old_style == self.unselected_cell_highlighted_value_2_label:
                new_style = self.selected_cell_highlighted_value_2_label
            else:
                # The style is unchanged
                new_style = old_style
            value_label.configure(style=new_style)

    def unselect_cell(self) -> None:
        """Un-highlight this cell."""
        self._selected = False
        self.configure(style=self.unselected_cell_frame)
        for value_label in self._domain:
            old_style = value_label.cget('style')
            if old_style == self.selected_cell_label:
                new_style = self.unselected_cell_label
            elif old_style == self.selected_cell_highlighted_value_1_label:
                new_style = self.unselected_cell_highlighted_value_1_label
            elif old_style == self.selected_cell_highlighted_value_2_label:
                new_style = self.unselected_cell_highlighted_value_2_label
            else:
                # The style is unchanged
                new_style = old_style
            value_label.configure(style=new_style)

    def select_value(self, value: int, highlight_type: int) -> None:
        """
        Highlight the specified value in this cell.

        :param value: The value to highlight.
        :param highlight_type: The type of highlighting to do. The color will depend on the type.
        """
        if highlight_type != 1 and highlight_type != 2:
            raise ValueError("Invalid highlight_type value")
        if self._selected:
            if highlight_type == 1:
                new_style = self.selected_cell_highlighted_value_1_label
            else:
                new_style = self.selected_cell_highlighted_value_2_label
        else:
            if highlight_type == 1:
                new_style = self.unselected_cell_highlighted_value_1_label
            else:
                new_style = self.unselected_cell_highlighted_value_2_label
        self._domain[value - 1].configure(style=new_style)

    def unselect_value(self, value: int) -> None:
        """
        Un-highlight the specified value in this cell.

        :param value: The value to stop highlighting.
        """
        if self._selected:
            new_style = self.selected_cell_label
        else:
            new_style = self.unselected_cell_label
        self._domain[value - 1].configure(style=new_style)


class AppMode(Enum):
    """The different modes that the application can be in."""
    INPUT = auto()
    WAIT = auto()
    SOLVE = auto()


class SudokuBoardBaseView(Frame):
    """
    The base class for SudokuBoardInputView and SudokuBoardSolverView. Extends Tk's Frame container.

    Public variables
    ----------------
    * board_size
    """

    def __init__(self, board_size: int, master=None, **kw) -> None:
        """
        :param board_size: The size of the board (9 or 4).
        :param master: The parent Tk container.
        """
        super().__init__(master, **kw)
        self.board_size = board_size

    def _make_gui(self, is_solver: bool) -> (list, dict):
        entries = []
        # These need to be instance variables so that mainloop will be able to reference the images when rendering
        images = {
            'c_separator_img': PhotoImage(file="assets/c_separator.png"),
            'h_separator_img': PhotoImage(file="assets/h_separator.png"),
            'v_separator_img': PhotoImage(file="assets/v_separator.png")
        }

        if self.board_size == 9:
            # Manually set position of separators to avoid convoluted logic
            # . _ . _ . _ .. _ . _ . _ .. _ . _ . _ .
            separator_indices = [0, 2, 4, 6, 7, 9, 11, 13, 14, 16, 18, 20]
            # Range is (number of cells) x (cell + separator) + (remaining separator) + (num of extra-thickness separators)
            range_end = self.board_size * 2 + 1 + 2
        elif self.board_size == 4:
            # board size is 4
            # . _ . _ .. _ . _ .
            separator_indices = [0, 2, 4, 5, 7, 9]
            range_end = self.board_size * 2 + 1 + 1
        else:
            raise ValueError("self.board_size has an invalid value")
        for row in range(0, range_end):
            cols = []
            for col in range(0, range_end):
                in_cell = False
                if row in separator_indices:
                    if col in separator_indices:
                        # We're at a point
                        item = TkLabel(self, image=images['c_separator_img'], borderwidth=0)
                    else:
                        # We're at a horizontal separator
                        item = TkLabel(self, image=images['h_separator_img'], borderwidth=0)
                else:
                    if col in separator_indices:
                        # We're at a vertical separator
                        item = TkLabel(self, image=images['v_separator_img'], borderwidth=0)
                    else:
                        # We're at the cell itself
                        in_cell = True
                        if is_solver:
                            item = SolverCell(self.board_size, self)
                        else:
                            item = Cell(self.board_size, self)
                if in_cell:
                    item.grid(row=row, column=col, sticky=NSEW)
                    cols.append(item)
                else:
                    item.grid(row=row, column=col)
            if len(cols) > 0:
                entries.append(cols)
        return entries, images


class SudokuBoardInputView(SudokuBoardBaseView):
    """
    Extends SudokuBoardBaseView to provide the view during the input mode.

    Public methods
    --------------
    * set_board
    * set_board_state
    * reset_board
    * clear_board
    * get_board
    """

    def __init__(self, board_size: int, master=None, **kw) -> None:
        """
        :param board_size: The size of the board (9 or 4).
        :param master: The parent Tk container.
        """
        super().__init__(board_size, master, **kw)
        self._entries, self._images = self._make_gui(is_solver=False)

    def set_board(self, values: Union[str, list], entry_disabled: bool) -> None:
        """
        Set the board given the provided values.

        :param values: A string or a list of integers to set the board.
        :param entry_disabled: Whether input should be disabled afterwards.
        """
        for row in range(self.board_size):
            for col in range(self.board_size):
                entry = self._entries[row][col]
                # Keep value blank if 0
                if isinstance(values, str):
                    value = values[row*self.board_size + col] if values[row*self.board_size + col] != '0' else ''
                else:
                    # values is a 1D list of digits
                    value = str(values[row*self.board_size + col]) if values[row*self.board_size + col] != 0 else ''
                # Needs to enabled to set text
                entry.configure(state=NORMAL)
                entry.delete('0', END)
                entry.insert(INSERT, value)
                if entry_disabled:
                    entry.configure(state=DISABLED)

    def set_board_state(self, enabled: bool) -> None:
        """
        Set whether input should be enabled for the board.

        :param enabled: Enable input.
        """
        if enabled:
            state = NORMAL
        else:
            state = DISABLED
        for row in self._entries:
            for entry in row:
                entry.configure(state=state)

    def reset_board(self, puzzle: Union[str, list]) -> None:
        """
        Reset the board to the provided puzzle.

        :param puzzle: A string or a list of integers to reset the board to.
        """
        self.set_board(values=puzzle, entry_disabled=False)

    def clear_board(self) -> None:
        """Clear the board."""
        self.set_board(values='0'*self.board_size*self.board_size, entry_disabled=False)

    def get_board(self) -> list:
        """
        Get the current board.

        :return: The list of values in row-major order.
        """
        puzzle_as_list = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                value = self._entries[row][col].get()
                digit = int(value) if value != '' else 0
                puzzle_as_list.append(digit)
        return puzzle_as_list


class SudokuBoardSolverView(SudokuBoardBaseView):
    """
    Extends SudokuBoardBaseView to provide the view during the solve mode.

    Public methods
    --------------
    * set_domains
    * highlight_current_variables
    * clear_all_highlighted_values
    * highlight_value_in_variable
    * reset_board
    """

    def __init__(self, board_size: int, master=None, **kw) -> None:
        """
        :param board_size: The size of the board (9 or 4).
        :param master: The parent tk container.
        """
        super().__init__(board_size, master, **kw)
        self._entries, self._images = self._make_gui(is_solver=True)

    def set_domains(self, domains: dict) -> None:
        """
        Set the domain values for each cell.

        :param domains: The domains for each variable.
        """
        for row in range(self.board_size):
            for col in range(self.board_size):
                variable_name = SudokuBoard.make_variable_name(row+1, col+1)
                entry = self._entries[row][col]
                entry.update_domain(domains[variable_name])

    def highlight_current_variables(self, variables: list) -> None:
        """
        Highlight the specified variables.

        :param variables: The variables to highlight.
        """
        for row in range(self.board_size):
            for col in range(self.board_size):
                self._entries[row][col].unselect_cell()
        for variable_name in variables:
            # Variable name starts at 1, 1
            row, col = SudokuBoard.get_row_col_from_variable_name(variable_name)
            self._entries[row - 1][col - 1].select_cell()

    def clear_all_highlighted_values(self) -> None:
        """Un-highlight all values in all cells."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                for default_value in range(self.board_size):
                    self._entries[row][col].unselect_value(default_value)

    def highlight_value_in_variable(self, variable: str, value: int, highlight_type: int) -> None:
        """
        Highlight specified value in specified variable.

        :param variable: The variable to look at.
        :param value: The value to highlight.
        :param highlight_type: The type of highlighting to do. The color will depend on the type.
        """
        row, col = SudokuBoard.get_row_col_from_variable_name(variable)
        self._entries[row - 1][col - 1].select_value(value, highlight_type)

    def reset_board(self, puzzle: list) -> None:
        """
        Set all domains to puzzle default and clear all selected cells/values.

        :param puzzle: The puzzle to reset the board to.
        """
        default_domain = [i+1 for i in range(self.board_size)]
        for row in range(self.board_size):
            for col in range(self.board_size):
                entry = self._entries[row][col]
                if puzzle[row * self.board_size + col] != 0:
                    values = [puzzle[row*self.board_size + col]]
                else:
                    values = default_domain
                entry.update_domain(values)
        self.highlight_current_variables(variables=[])
        self.clear_all_highlighted_values()


class OptionsPanelView(Frame):
    """
    Extends Frame to provide an options panel.

    Public methods
    --------------
    * get_algorithm_value
    * is_algorithm_option_selected
    * set_controls
    """

    def __init__(self, board_size: int, change_board_size_fn: Callable, master=None, **kw) -> None:
        """
        :param board_size: The size of the board (9 or 4).
        :param change_board_size_fn: The function to call when changing board size.
        :param master: The parent Tk container.
        """
        super().__init__(master, **kw)
        # A reference to the function is passed in so that the function call will not depend on the Tk hierarchy
        self.change_board_size_fn = change_board_size_fn
        # Need to mangle _options to avoid conflict with Tk's _options function
        self.__options, self._board_size, self._algorithm, self._algorithm_options = self._make_gui(board_size)

    def _make_gui(self, size: int) -> (dict, int, int, dict):
        Label(self, text="Options", font="TkHeadingFont 16").pack(fill=X)
        # Spacer
        Label(self).pack(side=TOP)
        board_size_frame = Frame(self)
        board_size_frame.pack(anchor=W)
        Label(board_size_frame, text="Board size:").pack(anchor=W)
        # Spacer
        Label(self).pack(side=TOP)
        algorithm_frame = Frame(self)
        algorithm_frame.pack(anchor=W)
        Label(algorithm_frame, text="Algorithm:").pack(anchor=W)
        # Spacer
        Label(self).pack(side=TOP)
        algorithm_options_frame = Frame(self)
        algorithm_options_frame.pack(anchor=W)
        # Assign to variable so they can be packed in order below
        algorithm_options_label = Label(algorithm_options_frame, text="Backtracking search options:")
        suv_label = Label(algorithm_options_frame, text="Select-Unassigned-Variable heuristic")
        odv_label = Label(algorithm_options_frame, text="Order-Domain-Values heuristic")
        inference_label = Label(algorithm_options_frame, text="Inference function")
        # Control variables for the radio buttons
        board_size = IntVar()
        # AlgorithmTypes enum is of type int
        algorithm = IntVar()
        options = {
            '9x9': Radiobutton(
                board_size_frame,
                text="9x9",
                command=self._on_press_board_size,
                variable=board_size,
                value=9),
            '4x4': Radiobutton(
                board_size_frame,
                text="4x4",
                command=self._on_press_board_size,
                variable=board_size,
                value=4),
            'AC3': Radiobutton(
                algorithm_frame,
                text="Constraint Propagation (AC-3)",
                variable=algorithm,
                command=(lambda: self._update_algorithm_checkbuttons('AC3')),
                # Value needs to be an int type, not an IntEnum. Otherwise, .get() will not work.
                value=AlgorithmTypes.AC3.value),
            'BacktrackingSearch': Radiobutton(
                algorithm_frame,
                text="Backtracking Search",
                variable=algorithm,
                command=(lambda: self._update_algorithm_checkbuttons('BacktrackingSearch')),
                value=AlgorithmTypes.BACKTRACKING_SEARCH.value)
        }
        algorithm_options = {}
        algorithm_options_list = [
            ('MRV', "Minimum-remaining-values heuristic",
             "Chooses the variable that has the least number of remaining values in its domain."),
            ('Degree', "Degree heuristic",
             "Chooses the variable that has the most constraints with the remaining unassigned variables."),
            ('LCV', "Least-constraining-value heuristic",
             "Orders values (in ascending order) by the number of values removed in the variable's neighbors if that "
             + "value is chosen."),
            ('ForwardChecking', "Forward checking",
             "Enforces arc consistency when a variable is assigned.")
        ]
        for key, description, tooltip_text in algorithm_options_list:
            algorithm_options[key] = IntVar()
            options[key] = Checkbutton(
                algorithm_options_frame,
                text=description,
                command=(lambda button=key: self._update_algorithm_checkbuttons(button)),
                variable=algorithm_options[key]
            )
            Hovertip(options[key], tooltip_text)
        # Set initial value
        board_size.set(size)
        options['9x9'].pack(anchor=W)
        options['4x4'].pack(anchor=W)
        options['AC3'].pack(anchor=W)
        options['BacktrackingSearch'].pack(anchor=W)
        algorithm_options_label.pack(anchor=W)
        suv_label.pack(anchor=W)
        options['MRV'].pack(anchor=W)
        options['Degree'].pack(anchor=W)
        odv_label.pack(anchor=W)
        options['LCV'].pack(anchor=W)
        inference_label.pack(anchor=W)
        options['ForwardChecking'].pack(anchor=W)
        return options, board_size, algorithm, algorithm_options

    def _on_press_board_size(self) -> None:
        # Call function in SudokuCSPSolver
        self.change_board_size_fn(self._board_size.get())

    def get_algorithm_value(self) -> int:
        """Get the value of the algorithm selected."""
        return self._algorithm.get()

    def _update_algorithm_checkbuttons(self, button: str) -> None:
        # Define updates based on the checkbutton or radiobutton being pressed
        algorithm_options = [
            'MRV',
            'Degree',
            'LCV',
            'ForwardChecking'
        ]
        if button == 'AC3':
            # Disable algorithm options
            for option in algorithm_options:
                self.__options[option].state(['disabled'])
        elif button == 'BacktrackingSearch':
            # Enable algorithm options
            for option in algorithm_options:
                self.__options[option].state(['!disabled'])
        elif button == 'MRV':
            if self._algorithm_options['MRV'].get() == 0:
                # If MRV heuristic is unchecked, make sure Degree heuristic is also unchecked.
                self._algorithm_options['Degree'].set(0)
            else:
                # If MRV heuristic is checked, make sure that forward checking is also checked.
                self._algorithm_options['ForwardChecking'].set(1)
        elif button == 'Degree':
            if self._algorithm_options['Degree'].get() == 1:
                # If Degree heuristic is checked, make sure MRV heuristic and forward checking are also checked.
                self._algorithm_options['MRV'].set(1)
                self._algorithm_options['ForwardChecking'].set(1)
        elif button == 'ForwardChecking':
            if self._algorithm_options['ForwardChecking'].get() == 0:
                # If forward checking is unchecked, make sure that MRV heuristic and Degree heuristic are also
                # unchecked.
                self._algorithm_options['MRV'].set(0)
                self._algorithm_options['Degree'].set(0)

    def is_algorithm_option_selected(self, option: str) -> bool:
        """
        Get whether the specified option is selected.

        :param option: The option to look up.
        :return: Whether the option is selected.
        """
        return self._algorithm_options[option].get() == 1

    def set_controls(self, enabled: bool) -> None:
        """
        Enable/disable the controls.

        :param enabled: Whether the controls should be enabled.
        """
        if enabled:
            state = ['!disabled']
        else:
            state = ['disabled']
        for option in self.__options:
            self.__options[option].state(state)
        if enabled:
            # If an algorithm is already selected, make sure to set the rest of the controls as expected.
            button_selected = None
            if self.get_algorithm_value() == AlgorithmTypes.AC3.value:
                button_selected = 'AC3'
            elif self.get_algorithm_value() == AlgorithmTypes.BACKTRACKING_SEARCH.value:
                button_selected = 'BacktrackingSearch'
            if button_selected:
                self._update_algorithm_checkbuttons(button_selected)


class StepControlButtons(Enum):
    """Possible buttons for the step controls."""
    FIRST = auto()
    PREVIOUS = auto()
    NEXT = auto()
    LAST = auto()


class InfoPanelSectionTypes(Enum):
    """Algorithm section types for the info panel."""
    none = auto()
    AC3 = auto()
    BACKTRACKING = auto()


class InfoPanelSectionsAC3(Enum):
    """Sections available for AC-3's info panel."""
    MESSAGE = auto()
    CURRENT_ARC = auto()
    CURRENT_QUEUE = auto()


class InfoPanelSectionsBacktracking(Enum):
    """Sections available for backtracking search's info panel."""
    MESSAGE = auto()
    CURRENT_ASSIGNMENT = auto()
    CURRENT_VARIABLE = auto()
    ORDERED_VALUES = auto()
    CURRENT_VALUE = auto()


class InfoPanelView(Frame):
    """
    Extends Frame to provide an info panel.

    Public methods
    --------------
    * set_current_step
    * set_total_steps
    * go_to_first_step
    * go_to_previous_step
    * go_to_next_step
    * go_to_last_step
    * set_step_controls
    * set_section
    * reset_panel
    * change_section

    Instance variables
    ------------------
    * current_step
    * go_to_step_fn
    """

    def __init__(self, go_to_step_fn: Callable, master=None, **kw) -> None:
        """
        :param go_to_step_fn: The function to call when going to a step.
        :param master: The parent Tk container.
        """
        super().__init__(master, **kw)
        # A reference to the function is passed in so that it can easily reference objects out of the current class's
        # scope.
        self.go_to_step_fn = go_to_step_fn
        # Don't automatically associate the value with the widget but set it manually, as users may enter invalid info.
        self.current_step = 1
        self._current_step_entry, self._total_steps, self._step_controls, self._sections, self._images = self._make_gui()
        # Keep track of which section should be visible (none by default)
        self._visible_section = InfoPanelSectionTypes.none
        self.change_section(InfoPanelSectionTypes.none)

    def _make_gui(self) -> (Entry, Label, dict, dict, dict):
        # These need to be instance variables so that mainloop will be able to reference the images when rendering
        images = {
            'first_step_img': PhotoImage(file="assets/step_first.png"),
            'previous_step_img': PhotoImage(file="assets/step_previous.png"),
            'next_step_img': PhotoImage(file="assets/step_next.png"),
            'last_step_img': PhotoImage(file="assets/step_last.png")
        }
        text_box_width = 40
        text_box_height = 10
        message_text_width = 300
        Label(self, text="Information", font="TkHeadingFont 16").pack(anchor=W)
        # Spacer
        Label(self).pack()
        # Step #/#
        step_frame = Frame(self)
        step_frame.pack()
        step_info_frame = Frame(self)
        step_info_frame.pack(anchor=W)
        Label(step_info_frame, text="Step: ").pack(side=LEFT)
        # Width will be set programmatically based on the total number of steps
        current_step_entry = Entry(step_info_frame, justify=RIGHT)
        current_step_entry.pack(side=LEFT)
        Hovertip(current_step_entry, "Current step")

        # We create a function variable instead of just using a lambda, as .bind() passes in the event as the argument
        def onEnter():
            self.go_to_step_fn(self._current_step_entry.get())
        current_step_entry.bind(
            '<Return>',
            (lambda event: onEnter())
        )
        Label(step_info_frame, text="/").pack(side=LEFT)
        total_steps = Label(step_info_frame)
        total_steps.pack(side=LEFT)
        Hovertip(total_steps, "Total steps")
        step_control_frame = Frame(self)
        step_control_frame.pack(anchor=W)
        # Dictionary of step controls
        step_controls = {
            StepControlButtons.FIRST: Button(
                step_control_frame, text="First", image=images['first_step_img'], command=self.go_to_first_step
            ),
            StepControlButtons.PREVIOUS: Button(
                step_control_frame, text="Previous", image=images['previous_step_img'], command=self.go_to_previous_step
            ),
            StepControlButtons.NEXT: Button(
                step_control_frame, text="Next", image=images['next_step_img'], command=self.go_to_next_step
            ),
            StepControlButtons.LAST: Button(
                step_control_frame, text="Last", image=images['last_step_img'], command=self.go_to_last_step
            )
        }
        step_controls[StepControlButtons.FIRST].pack(side=LEFT)
        step_controls[StepControlButtons.PREVIOUS].pack(side=LEFT)
        step_controls[StepControlButtons.NEXT].pack(side=LEFT)
        step_controls[StepControlButtons.LAST].pack(side=LEFT)
        Hovertip(step_controls[StepControlButtons.FIRST], "First step")
        Hovertip(step_controls[StepControlButtons.PREVIOUS], "Previous step")
        Hovertip(step_controls[StepControlButtons.NEXT], "Next step")
        Hovertip(step_controls[StepControlButtons.LAST], "Last step")

        # Spacer
        Label(self).pack()
        # Create a dictionary of updatable sections
        sections = {}

        # AC3 info section
        ac3_section_frame = Frame(self)
        ac3_section_frame.pack()
        # Step message
        message_frame = Frame(ac3_section_frame)
        message_frame.pack(anchor=W)
        Label(message_frame, text="Action:").pack(side=LEFT, anchor=N)
        message_text = Label(message_frame, wraplength=message_text_width)
        message_text.pack(side=LEFT)
        # Current arc
        arc_frame = Frame(ac3_section_frame)
        arc_frame.pack(anchor=W)
        Label(arc_frame, text="Current arc:").pack(side=LEFT)
        arc_text = Label(arc_frame)
        arc_text.pack(side=LEFT)
        # Current queue
        queue_frame = Frame(ac3_section_frame)
        queue_frame.pack(anchor=W)
        Label(queue_frame, text="Current queue:").pack(anchor=W)
        queue_text = ScrolledText(queue_frame, width=text_box_width, height=text_box_height)
        queue_text.pack()
        queue_text.configure(state=DISABLED)
        # Keep updatable sections
        sections[InfoPanelSectionTypes.AC3] = ac3_section_frame
        sections[InfoPanelSectionsAC3.MESSAGE] = message_text
        sections[InfoPanelSectionsAC3.CURRENT_ARC] = arc_text
        sections[InfoPanelSectionsAC3.CURRENT_QUEUE] = queue_text

        # Backtracking search info section
        backtracking_section_frame = Frame(self)
        backtracking_section_frame.pack()
        # Step message
        message_frame = Frame(backtracking_section_frame)
        message_frame.pack(anchor=W)
        Label(message_frame, text="Action:").pack(side=LEFT, anchor=N)
        message_text = Label(message_frame, wraplength=message_text_width)
        message_text.pack(side=LEFT)
        # Current assignment
        assignment_frame = Frame(backtracking_section_frame)
        assignment_frame.pack(anchor=W)
        Label(assignment_frame, text="Current assignment:").pack(anchor=W)
        assignment_text = ScrolledText(assignment_frame, width=text_box_width, height=text_box_height)
        assignment_text.pack()
        assignment_text.configure(state=DISABLED)
        # Current variable
        variable_frame = Frame(backtracking_section_frame)
        variable_frame.pack(anchor=W)
        Label(variable_frame, text="Current variable:").pack(side=LEFT)
        variable_text = Label(variable_frame)
        variable_text.pack(side=LEFT)
        # Ordered values
        ordered_values_frame = Frame(backtracking_section_frame)
        ordered_values_frame.pack(anchor=W)
        Label(ordered_values_frame, text="Ordered values:").pack(side=LEFT)
        ordered_values_text = Label(ordered_values_frame)
        ordered_values_text.pack(side=LEFT)
        # Current value
        value_frame = Frame(backtracking_section_frame)
        value_frame.pack(anchor=W)
        Label(value_frame, text="Current value:").pack(side=LEFT)
        value_text = Label(value_frame)
        value_text.pack(side=LEFT)
        # Keep updatable sections
        sections[InfoPanelSectionTypes.BACKTRACKING] = backtracking_section_frame
        sections[InfoPanelSectionsBacktracking.MESSAGE] = message_text
        sections[InfoPanelSectionsBacktracking.CURRENT_ASSIGNMENT] = assignment_text
        sections[InfoPanelSectionsBacktracking.CURRENT_VARIABLE] = variable_text
        sections[InfoPanelSectionsBacktracking.ORDERED_VALUES] = ordered_values_text
        sections[InfoPanelSectionsBacktracking.CURRENT_VALUE] = value_text

        return current_step_entry, total_steps, step_controls, sections, images

    def set_current_step(self, step: int) -> None:
        """
        Set the current step.

        :param step: The current step.
        """
        self.current_step = step
        self._current_step_entry.delete('0', END)
        self._current_step_entry.insert(INSERT, str(step))

    def set_total_steps(self, num_steps: int) -> None:
        """
        Set the total number of steps and the size of the current step entry.

        :param num_steps: Total number of steps.
        """
        total_steps_string = str(num_steps)
        # Give a little more room for better aesthetics
        self._current_step_entry.configure(width=len(total_steps_string)+1)
        self._total_steps.configure(text=total_steps_string)

    def go_to_first_step(self, reset_message: bool = False) -> None:
        """
        Go to the first step.

        :param reset_message: Whether to reset the message text.
        """
        self.go_to_step_fn('1', reset_message)

    def go_to_previous_step(self) -> None:
        """Go to the previous step."""
        self.go_to_step_fn(str(self.current_step - 1))

    def go_to_next_step(self) -> None:
        """Go to the next step."""
        self.go_to_step_fn(str(self.current_step + 1))

    def go_to_last_step(self) -> None:
        """Go to the last step."""
        self.go_to_step_fn(self._total_steps.cget('text'))

    def set_step_controls(self) -> None:
        """Set the step controls in accordance with the current step."""
        # Make sure that controls are set correctly
        total_steps = int(self._total_steps.cget('text'))
        if total_steps <= 1:
            self._step_controls[StepControlButtons.FIRST].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.PREVIOUS].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.NEXT].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.LAST].state(['disabled', '!focus'])
        elif self.current_step == 1:
            self._step_controls[StepControlButtons.FIRST].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.PREVIOUS].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.NEXT].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.LAST].state(['!disabled', '!focus'])
        elif self.current_step == total_steps:
            self._step_controls[StepControlButtons.FIRST].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.PREVIOUS].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.NEXT].state(['disabled', '!focus'])
            self._step_controls[StepControlButtons.LAST].state(['disabled', '!focus'])
        else:
            self._step_controls[StepControlButtons.FIRST].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.PREVIOUS].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.NEXT].state(['!disabled', '!focus'])
            self._step_controls[StepControlButtons.LAST].state(['!disabled', '!focus'])

    def set_section(self, section: Union[InfoPanelSectionsAC3, InfoPanelSectionsBacktracking], obj) -> None:
        """
        Set the information to display on the info panel.

        :param section: The section to update.
        :param obj: The information used for the update.
        """
        if self._visible_section is InfoPanelSectionTypes.AC3:
            if section is InfoPanelSectionsAC3.MESSAGE:
                obj_string = obj if obj is not None else ""
                self._sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsAC3.CURRENT_ARC:
                obj_string = "{}, {}".format(obj[0], obj[1]) if obj is not None and len(obj) == 2 else ""
                self._sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsAC3.CURRENT_QUEUE:
                obj_string = ""
                if obj is not None:
                    obj_list = ["{}, {}".format(i[0], i[1]) for i in list(obj)]
                    obj_string = '\n'.join(obj_list)
                # Need to enable to set text
                self._sections[section].configure(state=NORMAL)
                # First line, first character to end of text
                self._sections[section].delete('1.0', END)
                self._sections[section].insert(INSERT, obj_string)
                self._sections[section].configure(state=DISABLED)
            else:
                raise ValueError("No behavior defined for given section")
        elif self._visible_section is InfoPanelSectionTypes.BACKTRACKING:
            if section is InfoPanelSectionsBacktracking.MESSAGE:
                obj_string = obj if obj is not None else ""
                self._sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.CURRENT_ASSIGNMENT:
                obj_string = ""
                if obj is not None:
                    # We sort the result so it's easier for a human to read
                    obj_list = ["'{}'={}".format(var_name, obj[var_name]) for var_name in sorted(obj.keys())]
                    obj_string = '\n'.join(obj_list)
                # Need to enable to set text
                self._sections[section].configure(state=NORMAL)
                # First line, first character to end of text
                self._sections[section].delete('1.0', END)
                self._sections[section].insert(INSERT, obj_string)
                self._sections[section].configure(state=DISABLED)
            elif section is InfoPanelSectionsBacktracking.CURRENT_VARIABLE:
                obj_string = obj if obj is not None else ""
                self._sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.ORDERED_VALUES:
                obj_string = ""
                if obj is not None:
                    obj_list = [str(i) for i in obj]
                    obj_string = ', '.join(obj_list)
                self._sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.CURRENT_VALUE:
                obj_string = str(obj) if obj is not None else ""
                self._sections[section].configure(text=obj_string)

    def reset_panel(self) -> None:
        """Reset state of all widgets in the info panel."""
        self.current_step = 1
        self._current_step_entry.delete('0', END)
        self.set_total_steps(0)
        self.set_step_controls()
        if self._visible_section is InfoPanelSectionTypes.AC3:
            for section in InfoPanelSectionsAC3:
                self.set_section(section, None)
        elif self._visible_section is InfoPanelSectionTypes.BACKTRACKING:
            for section in InfoPanelSectionsBacktracking:
                self.set_section(section, None)
        else:
            pass

    def change_section(self, section: InfoPanelSectionTypes) -> None:
        """
        Change the algorithm section.

        :param section: The algorithm section to display.
        """
        self._visible_section = section
        if section is InfoPanelSectionTypes.AC3:
            self._sections[InfoPanelSectionTypes.BACKTRACKING].pack_forget()
            self._sections[InfoPanelSectionTypes.AC3].pack()
        elif section is InfoPanelSectionTypes.BACKTRACKING:
            self._sections[InfoPanelSectionTypes.AC3].pack_forget()
            self._sections[InfoPanelSectionTypes.BACKTRACKING].pack()
        else:
            self._sections[InfoPanelSectionTypes.AC3].pack_forget()
            self._sections[InfoPanelSectionTypes.BACKTRACKING].pack_forget()


class SudokuCSPSolver:
    """
    Main class for the application.

    Public methods
    --------------
    * run
    * solve
    * puzzle_list_to_string
    * result_dict_to_string
    * reset
    * clear
    * reset_message
    * set_message
    * get_message
    * change_board_size
    * set_controls
    * change_board_type
    * change_panel
    * go_to_step
    * validate_options

    Instance variables
    ------------------
    * board_size
    * entry_disabled
    * puzzle
    * history
    * selected_algorithm
    * csp
    * solving
    * wait_time
    * algorithm_result
    """

    def __init__(self) -> None:
        self.board_size = 9
        if len(sys.argv) == 2:
            if len(sys.argv[1]) == 4*4:
                self.board_size = 4
            elif len(sys.argv[1]) == 9*9:
                self.board_size = 9
            else:
                raise ValueError("The initial puzzle string has an invalid length.")
        self._root, self._board_views, self._main_panel, self._message, self._buttons = self._make_gui()
        initial_board = str(self.board_size)+'_'+AppMode.INPUT.name
        self._board_view = self._board_views[initial_board]
        # Hide the board(s) that are not active
        for view in self._board_views:
            if view != initial_board:
                self._board_views[view].grid_remove()
        # Only show the options panel
        for panel in self._main_panel:
            if not isinstance(self._main_panel[panel], OptionsPanelView):
                self._main_panel[panel].grid_remove()
        self.entry_disabled = False
        # Fill out cells with initial values if applicable
        if len(sys.argv) == 2:
            self._board_view.set_board(values=sys.argv[1], entry_disabled=self.entry_disabled)
        # Store the current puzzle
        self.puzzle = None
        # Store history of solver
        self.history = None
        self.selected_algorithm = None
        # Keep CSP after it's generated to be able to access its properties from methods other than solve()
        self.csp = None
        # Track whether the algorithm is currently running
        self.solving = False
        # Wait 250 ms between each UI update
        self.wait_time = 250
        self.algorithm_result = None

    def run(self) -> None:
        """Main loop of application."""
        self._root.mainloop()

    def _make_gui(self) -> (Tk, dict, dict, Label, dict):
        # Set dimensions for the two main panels of the application, to allow showing/hiding widgets without changing
        # the size of the window.
        board_frame_height = 500
        board_frame_width = 500
        panel_frame_width = 375

        root = Tk()
        # Set the background of all elements to the same color for a consistent look.
        s = Style()
        default_bg_color = s.lookup(style='TButton', option='background')
        s.configure('Toolbar.TFrame', background=default_bg_color)

        upper_part = Frame(root)
        upper_part.pack()
        # Draw all boards (4x4 and 9x9), hiding the inactive board later
        # These need to use the grid geometry manager so that the items can be hidden and shown without losing their
        # place.
        # Set height/width so that the container size is kept no matter which board is used.
        board_outer_frame = Frame(upper_part, height=board_frame_height, width=board_frame_width)
        board_outer_frame.pack(side=LEFT)
        # Stop the slaves' geometry manager from propagating the size to the master.
        board_outer_frame.pack_propagate(False)
        # We need an inner frame to center the container used by the grid geometry manager.
        board_inner_frame = Frame(board_outer_frame)
        board_inner_frame.pack(expand=YES)
        board_views = {}
        for size_index in range(len(SudokuBoard.board_sizes)):
            size = SudokuBoard.board_sizes[size_index]
            board_views[str(size)+'_'+AppMode.INPUT.name] = SudokuBoardInputView(size, board_inner_frame)
            board_views[str(size)+'_'+AppMode.INPUT.name].grid(row=0, column=size_index)
            board_views[str(size)+'_'+AppMode.SOLVE.name] = SudokuBoardSolverView(size, board_inner_frame)
            board_views[str(size)+'_'+AppMode.SOLVE.name].grid(row=0, column=size_index)
        # Main panel
        # Similar trick as with the board frame, but no inner frame as the content does not need to be centered.
        panel_frame = Frame(upper_part, width=panel_frame_width)
        panel_frame.pack(side=LEFT, expand=YES, fill=BOTH)
        panel_frame.grid_propagate(False)
        main_panel = {
            'options_panel': OptionsPanelView(self.board_size, self.change_board_size, panel_frame),
            'info_panel': InfoPanelView(self.go_to_step, panel_frame)
        }
        column_index = len(SudokuBoard.board_sizes)
        for panel in main_panel:
            main_panel[panel].grid(row=0, column=column_index, padx=20, pady=20)
            column_index += 1

        # Message bar
        message_bar = Frame(root)
        message_bar.pack(fill=BOTH)
        message = Label(message_bar, anchor='center')
        message.pack(expand=YES, fill=BOTH)
        # Toolbar
        toolbar_outer = Frame(root, style='Toolbar.TFrame')
        toolbar_outer.pack(fill=BOTH)
        toolbar = Frame(toolbar_outer, style='Toolbar.TFrame')
        toolbar.pack()
        buttons = {
            'solve_button': Button(toolbar, text="Solve", command=self.solve),
            'reset_button': Button(toolbar, text="Reset solver", command=self.reset),
            'clear_button': Button(toolbar, text="Clear all cells", command=self.clear)
        }
        # ttk buttons have more complex states than can be handled by the .configure command
        buttons['reset_button'].state(['disabled'])
        buttons['solve_button'].pack(side=LEFT, padx=5, pady=10)
        buttons['reset_button'].pack(side=LEFT, padx=5, pady=10)
        buttons['clear_button'].pack(side=LEFT, padx=5, pady=10)
        root.title("Sudoku CSP Solver")
        return root, board_views, main_panel, message, buttons

    def solve(self) -> None:
        """change to solve mode and run the algorithm in another thread."""
        # Remove any existing messages
        self.reset_message()
        # Make sure options are valid
        if not self.validate_options():
            return
        # Read cells and create Sudoku board
        puzzle_as_list = self._board_view.get_board()
        # Save off board. We don't use SudokuBoard.to_list() as it depends on a valid puzzle.
        self.puzzle = puzzle_as_list
        # Create the Sudoku
        board = SudokuBoard(size=self.board_size)
        try:
            board.set_cells(puzzle_as_list)
        except ValueError:
            self.set_message(text="There are duplicate values in a row, column, or region.", error=True)
            return
        self.solving = True
        self.set_controls(AppMode.WAIT)
        # Instead of changing the board type, disable input in the INPUT view.
        self._board_view.set_board_state(enabled=False)
        # Solve using selected options
        self.selected_algorithm = AlgorithmTypes(self._main_panel['options_panel'].get_algorithm_value())
        self.csp = board.generate_csp()
        if self.selected_algorithm == AlgorithmTypes.AC3:
            algorithm_runner = AC3(self.csp, record_history=True)
        elif self.selected_algorithm == AlgorithmTypes.BACKTRACKING_SEARCH:
            suv_heuristic = SelectUnassignedVariableHeuristics.none
            odv_heuristic = OrderDomainValuesHeuristics.none
            inference_fn = InferenceFunctions.none
            if self._main_panel['options_panel'].is_algorithm_option_selected('MRV'):
                suv_heuristic = SelectUnassignedVariableHeuristics.MRV
            if self._main_panel['options_panel'].is_algorithm_option_selected('Degree'):
                suv_heuristic = SelectUnassignedVariableHeuristics.DEGREE_HEURISTIC
            if self._main_panel['options_panel'].is_algorithm_option_selected('LCV'):
                odv_heuristic = OrderDomainValuesHeuristics.LCV
            if self._main_panel['options_panel'].is_algorithm_option_selected('ForwardChecking'):
                inference_fn = InferenceFunctions.FORWARD_CHECKING
            algorithm_runner = BacktrackingSearch(
                csp=self.csp,
                select_unassigned_variable_heuristic=suv_heuristic,
                order_domain_values_heuristic=odv_heuristic,
                inference_function=inference_fn,
                record_history=True
            )
        else:
            raise ValueError("Invalid value for algorithm")
        # Run the algorithm in another thread to prevent blocking of UI
        _thread.start_new_thread(self._run_algorithm, (algorithm_runner,))
        # Wait for the algorithm to finish then display the results
        self._root.after(ms=self.wait_time, func=self._wait_for_results)

    def _run_algorithm(self, algorithm_runner: Union[AC3, BacktrackingSearch]) -> None:
        self.algorithm_result = algorithm_runner.run()
        # Store history in instance so it will be accessible to other methods
        self.history = algorithm_runner.history
        self.solving = False

    def _wait_for_results(self):
        if self.solving:
            prefix = "Solving"
            if not self.get_message().startswith(prefix):
                self.set_message(prefix + "   ")
            elif self.get_message() == prefix + "   ":
                self.set_message(prefix + ".  ")
            elif self.get_message() == prefix + ".  ":
                self.set_message(prefix + ".. ")
            elif self.get_message() == prefix + ".. ":
                self.set_message(prefix + "...")
            else:
                self.set_message(prefix + "   ")
            self._root.after(ms=self.wait_time, func=self._wait_for_results)
        else:
            self.set_controls(AppMode.SOLVE)
            # Change to solver view
            self.change_board_type(AppMode.SOLVE)
            # Make sure that the board is cleared of any previous solves
            self._board_view.reset_board(self.puzzle)
            # Change to information panel
            self.change_panel(InfoPanelView)
            # Change information panel's section to match the algorithm
            if self.selected_algorithm is AlgorithmTypes.AC3:
                section_type = InfoPanelSectionTypes.AC3
            elif self.selected_algorithm is AlgorithmTypes.BACKTRACKING_SEARCH:
                section_type = InfoPanelSectionTypes.BACKTRACKING
            else:
                section_type = InfoPanelSectionTypes.none
            self._main_panel['info_panel'].change_section(section_type)
            # Both AC3 and backtracking search can return no consistent assignment
            if self.algorithm_result is None:
                self.set_message(text="The search algorithm could not find a consistent assignment.", error=True)
            elif self.selected_algorithm is AlgorithmTypes.AC3:
                # AC3 can return a partial assignment
                partial_assignment = False
                for variable_name in self.algorithm_result.keys():
                    if len(self.algorithm_result[variable_name]) > 1:
                        partial_assignment = True
                        break
                if partial_assignment:
                    self.set_message(text="AC3 algorithm returned a partial assignment.", error=True)
            num_steps = len(self.history)
            self._main_panel['info_panel'].set_total_steps(num_steps)
            # Set first step in history
            self._main_panel['info_panel'].go_to_first_step(reset_message=False)

    @staticmethod
    def puzzle_list_to_string(puzzle: list) -> str:
        """
        Convert the puzzle from a list to a string.

        :param puzzle: The puzzle as a list of integers.
        :return: The puzzle as a string of integers.
        """
        # Turn integers to strings if necessary
        temp_list = [str(puzzle[i]) for i in range(len(puzzle))]
        puzzle_string = ''.join(temp_list)
        return puzzle_string

    @staticmethod
    def result_dict_to_string(result: dict) -> str:
        """
        Convert a result dictionary to a string.

        :param result: The result as a dictionary.
        :return: The result as a string.
        """
        result_list = []
        for var_name in sorted(result):
            digit = result[var_name][0] if isinstance(result[var_name], list) else result[var_name]
            result_list.append(str(digit))
        result_string = ''.join(result_list)
        return result_string

    def reset(self) -> None:
        """Reset the application from the solve mode to the input mode."""
        # Remove any existing messages
        self.reset_message()
        self.set_controls(AppMode.INPUT)
        self.change_board_type(AppMode.INPUT)
        self._board_view.reset_board(self.puzzle)
        self._main_panel['info_panel'].reset_panel()
        self.change_panel(OptionsPanelView)

    def clear(self) -> None:
        """Clear all cells of the Sudoku board."""
        # Remove any existing messages
        self.reset_message()
        self._board_view.clear_board()

    def reset_message(self) -> None:
        """Reset the message UI element."""
        self._message.configure(foreground='black', text="")

    def set_message(self, text: str, error: bool = False) -> None:
        """
        Set the message UI element.

        :param text: The text to set.
        :param error: Whether the message is an error.
        """
        color = 'red' if error else 'black'
        self._message.configure(foreground=color, text=text)

    def get_message(self) -> str:
        """
        Get the current message being shown.

        :return: The current message.
        """
        return self._message.cget('text')

    def change_board_size(self, size: int) -> None:
        """
        Change the size of the board.

        :param size: The size of the board (9 or 4).
        """
        # Hide current board
        self._board_view.grid_remove()
        # Show new board
        self.board_size = size
        self._board_view = self._board_views[str(self.board_size) + '_' + AppMode.INPUT.name]
        self._board_view.grid()

    def set_controls(self, mode: AppMode) -> None:
        """
        Set the application's controls based on the mode.

        :param mode: The current mode of the application.
        """
        if mode == AppMode.WAIT:
            # Need to remove keyboard focus when disabling button being pressed
            self._buttons['solve_button'].state(['disabled', '!focus'])
            self._buttons['reset_button'].state(['disabled'])
            self._buttons['clear_button'].state(['disabled'])
            self._main_panel['options_panel'].set_controls(enabled=False)
        elif mode == AppMode.SOLVE:
            self.entry_disabled = True
            self._buttons['solve_button'].state(['disabled', '!focus'])
            self._buttons['reset_button'].state(['!disabled'])
            self._buttons['clear_button'].state(['disabled'])
        else:
            # Mode == AppMode.INPUT
            self.entry_disabled = False
            self._buttons['solve_button'].state(['!disabled'])
            self._buttons['reset_button'].state(['disabled', '!focus'])
            self._buttons['clear_button'].state(['!disabled'])
            self._main_panel['options_panel'].set_controls(enabled=True)

    def change_board_type(self, mode: AppMode) -> None:
        """
        Change the type of the Sudoku board UI element based on the mode.

        :param mode: The current mode of the application.
        """
        # Hide current board
        self._board_view.grid_remove()
        # Show new board
        self._board_view = self._board_views["{}_{}".format(str(self.board_size), mode.name)]
        self._board_view.grid()

    def change_panel(self, panel_type: type) -> None:
        """
        Change the main panel.

        :param panel_type: The panel type to change to.
        """
        for panel in self._main_panel:
            if not isinstance(self._main_panel[panel], panel_type):
                self._main_panel[panel].grid_remove()
            else:
                self._main_panel[panel].grid()

    def go_to_step(self, step_string: str, reset_message: bool = True) -> None:
        """
        Go to the specified step in the algorithm run's history.

        :param step_string: A string representation of the step to go to.
        :param reset_message: Whether to reset the message text.
        """
        # Clear message first
        if reset_message:
            self.reset_message()
        # Validate input
        try:
            step = int(step_string)
        except ValueError:
            self.set_message("Step is not valid.", error=True)
            return
        if step <= 0 or step > len(self.history):
            self.set_message("Step is not valid.", error=True)
            return
        history_step = self.history[step-1]
        # Set info panel
        self._main_panel['info_panel'].set_current_step(step)
        self._main_panel['info_panel'].set_step_controls()
        if self.selected_algorithm is AlgorithmTypes.AC3:
            # Set board
            self._board_view.highlight_current_variables(history_step[AC3HistoryItems.CURRENT_ARC])
            self._board_view.set_domains(history_step[AC3HistoryItems.DOMAINS])
            # Change all necessary widgets to reflect info in new step
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.MESSAGE,
                history_step[AC3HistoryItems.MESSAGE]
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.CURRENT_ARC,
                history_step[AC3HistoryItems.CURRENT_ARC]
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.CURRENT_QUEUE,
                history_step[AC3HistoryItems.CURRENT_QUEUE]
            )
        elif self.selected_algorithm is AlgorithmTypes.BACKTRACKING_SEARCH:
            # Set board
            # Clear any previous highlighted values
            self._board_view.clear_all_highlighted_values()
            current_variable = history_step[BacktrackingSearchHistoryItems.CURRENT_VARIABLE]
            if current_variable is not None:
                highlight_variables = [current_variable]
            else:
                # Pass in an empty list to deselect all variables
                highlight_variables = []
            self._board_view.highlight_current_variables(highlight_variables)
            current_value = history_step[BacktrackingSearchHistoryItems.CURRENT_VALUE]
            if current_value is not None:
                self._board_view.highlight_value_in_variable(current_variable, current_value, highlight_type=1)
            # Set assignment after current value so that when the current value gets assigned to the variable, it will
            # be highlighted as an assignment.
            assignment = history_step[BacktrackingSearchHistoryItems.CURRENT_ASSIGNMENT]
            for variable in assignment.keys():
                self._board_view.highlight_value_in_variable(variable, assignment[variable], highlight_type=2)
            domains = history_step[BacktrackingSearchHistoryItems.INFERENCES]
            if domains is None:
                # Show all values if there's no inferencing
                domains = self.csp.get_all_domains()
            self._board_view.set_domains(domains)
            # Change all necessary widgets to reflect info in new step
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.MESSAGE,
                history_step[BacktrackingSearchHistoryItems.MESSAGE]
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_ASSIGNMENT,
                assignment
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_VARIABLE,
                current_variable
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.ORDERED_VALUES,
                history_step[BacktrackingSearchHistoryItems.ORDERED_VALUES]
            )
            self._main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_VALUE,
                current_value
            )
        else:
            raise ValueError("No defined behavior for selected_algorithm value")

    def validate_options(self) -> bool:
        """
        Validate the algorithm options selected.

        :return: Whether the options selected is a valid combination.
        """
        # Use the raw Enum value so we can check if it's not in AlgorithmTypes
        selected_algorithm = self._main_panel['options_panel'].get_algorithm_value()
        if selected_algorithm != AlgorithmTypes.AC3 and selected_algorithm != AlgorithmTypes.BACKTRACKING_SEARCH:
            self.set_message("No algorithm selected", error=True)
            return False
        if self.board_size == 9 and selected_algorithm == AlgorithmTypes.BACKTRACKING_SEARCH and \
                not self._main_panel['options_panel'].is_algorithm_option_selected('MRV'):
            self.set_message("Minimum-remaining-values heuristic must be selected for backtracking search when the " +
                             "board size is 9x9", error=True)
            return False
        return True


def main():
    solver = SudokuCSPSolver()
    solver.run()


if __name__ == "__main__":
    main()
