from tkinter import *
from tkinter.scrolledtext import *
from tkinter.ttk import *
# Re-import tkinter's Label so we can use it even when it's overridden by ttk's import
from tkinter import Label as TkLabel
from sudoku_board import SudokuBoard
from algorithms import AC3, BacktrackingSearch, AC3HistoryItems, AlgorithmTypes, SelectUnassignedVariableHeuristics, \
    OrderDomainValuesHeuristics, InferenceFunctions, BacktrackingSearchHistoryItems
from enum import Enum, auto


class Cell(Entry):
    def __init__(self, max_digit: int, master=None):
        super().__init__(
            master,
            width=1,
            font="Helvetica 20",
            justify="center"
        )
        # Only allow 1 digit between 1-board_size in entry
        # Validation documentation under http://tcl.tk/man/tcl8.6/TkCmd/entry.htm#M16
        command = (self.register(self.on_validate), "%P")
        self.configure(validate="key", validatecommand=command)
        self.max_digit = max_digit

    def on_validate(self, new_value):
        """Validate that the input is a digit between 1 and the board size (4 or 9)."""
        if new_value == "":
            return True
        try:
            value = int(new_value)
            if 0 < value <= self.max_digit:
                return True
            else:
                return False
        except ValueError:
            return False


class SolverCell(Frame):
    """Class that draws each cell in the solving phase."""
    # Style names
    unselected_cell_frame = 'Cell.TFrame'
    selected_cell_frame = 'SelectedCell.TFrame'
    unselected_cell_label = 'Cell.TLabel'
    unselected_cell_highlighted_value_1_label = 'Cell_HighlightValue1.TLabel'
    unselected_cell_highlighted_value_2_label = 'Cell_HighlightValue2.TLabel'
    selected_cell_label = 'SelectedCell.TLabel'
    selected_cell_highlighted_value_1_label = 'SelectedCell_HighlightValue1.TLabel'
    selected_cell_highlighted_value_2_label = 'SelectedCell_HighlightValue2.TLabel'

    def __init__(self, max_digit: int, master=None, **kw):
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
        self.max_digit = max_digit
        self.domain = self.make_gui()
        # Flag to specify whether this cell is currently selected
        self.selected = False
        # Set to unselected by default
        self.unselect_cell()

    def make_gui(self):
        domain = []
        digit = 1
        # Positioning is not ideal (horizontal spacing is a bit too narrow), but this seems to be the best Tk can do.
        if self.max_digit == 9:
            range_end = 3
            font = "Helvetica 7"
            x_padding = 2
        elif self.max_digit == 4:
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

    def update_domain(self, new_domain: list):
        for digit_index in range(self.max_digit):
            digit = digit_index+1
            if digit in new_domain:
                # Make sure that the digit is shown if it's in the new domain
                self.domain[digit_index].configure(text=str(digit))
            else:
                # Make sure that the digit is not shown if it's not in the new domain
                self.domain[digit_index].configure(text=" ")

    def select_cell(self):
        self.selected = True
        self.configure(style=self.selected_cell_frame)
        for value_label in self.domain:
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

    def unselect_cell(self):
        self.selected = False
        self.configure(style=self.unselected_cell_frame)
        for value_label in self.domain:
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

    def select_value(self, value, highlight_type: int):
        if highlight_type != 1 and highlight_type != 2:
            raise ValueError("Invalid highlight_type value")
        if self.selected:
            if highlight_type == 1:
                new_style = self.selected_cell_highlighted_value_1_label
            else:
                new_style = self.selected_cell_highlighted_value_2_label
        else:
            if highlight_type == 1:
                new_style = self.unselected_cell_highlighted_value_1_label
            else:
                new_style = self.unselected_cell_highlighted_value_2_label
        self.domain[value-1].configure(style=new_style)

    def unselect_value(self, value):
        if self.selected:
            new_style = self.selected_cell_label
        else:
            new_style = self.unselected_cell_label
        self.domain[value-1].configure(style=new_style)


class AppMode(Enum):
    INPUT = auto()
    SOLVE = auto()


class SudokuBoardBaseView(Frame):
    def __init__(self, board_size: int, master=None, **kw):
        super().__init__(master, **kw)
        self.board_size = board_size

    def make_gui(self, is_solver) -> tuple:
        """Create the tk GUI elements using grid geometry manager and images of separators."""
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
    def __init__(self, board_size: int, master=None, **kw):
        super().__init__(board_size, master, **kw)
        self.entries, self.images = self.make_gui(is_solver=False)

    def set_board(self, values, entry_disabled: bool) -> None:
        """Tk commands to set the board."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                entry = self.entries[row][col]
                # Keep value blank if 0
                if type(values) is str:
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

    def reset_board(self, puzzle) -> None:
        """Reset the board UI elements."""
        self.set_board(values=puzzle, entry_disabled=False)

    def clear_board(self) -> None:
        """Clear board UI elements."""
        self.set_board(values='0'*self.board_size*self.board_size, entry_disabled=False)

    def get_board(self) -> list:
        puzzle_as_list = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                value = self.entries[row][col].get()
                digit = int(value) if value != '' else 0
                puzzle_as_list.append(digit)
        return puzzle_as_list


class SudokuBoardSolverView(SudokuBoardBaseView):
    def __init__(self, board_size: int, master=None, **kw):
        super().__init__(board_size, master, **kw)
        self.entries, self.images = self.make_gui(is_solver=True)

    def set_domains(self, domains: dict):
        """Set the domain values for each cell."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                variable_name = SudokuBoard.make_variable_name(row+1, col+1)
                entry = self.entries[row][col]
                entry.update_domain(domains[variable_name])

    def highlight_current_variables(self, variables: list) -> None:
        for row in range(self.board_size):
            for col in range(self.board_size):
                self.entries[row][col].unselect_cell()
        for variable_name in variables:
            # Variable name starts at 1, 1
            row, col = SudokuBoard.get_row_col_from_variable_name(variable_name)
            self.entries[row-1][col-1].select_cell()

    def clear_all_highlighted_values(self) -> None:
        for row in range(self.board_size):
            for col in range(self.board_size):
                for default_value in range(self.board_size):
                    self.entries[row][col].unselect_value(default_value)

    def highlight_value_in_variable(self, variable, value: int, highlight_type: int) -> None:
        row, col = SudokuBoard.get_row_col_from_variable_name(variable)
        self.entries[row-1][col-1].select_value(value, highlight_type)

    def reset_board(self, puzzle: list) -> None:
        """Set all domains to puzzle default and clear all selected cells/values"""
        default_domain = [i+1 for i in range(self.board_size)]
        for row in range(self.board_size):
            for col in range(self.board_size):
                entry = self.entries[row][col]
                if puzzle[row * self.board_size + col] != 0:
                    values = [puzzle[row*self.board_size + col]]
                else:
                    values = default_domain
                entry.update_domain(values)
        self.highlight_current_variables(variables=[])
        self.clear_all_highlighted_values()


class OptionsPanelView(Frame):
    def __init__(self, board_size: int, change_board_size_fn, master=None, **kw):
        super().__init__(master, **kw)
        # A reference to the function is passed in so that the function call will not depend on the Tk hierarchy
        self.change_board_size_fn = change_board_size_fn
        self.options, self.board_size, self.algorithm, self.algorithm_options = self.make_gui(board_size)

    def make_gui(self, size: int) -> (dict, int, int, dict):
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
                command=self.on_press_board_size,
                variable=board_size,
                value=9),
            '4x4': Radiobutton(
                board_size_frame,
                text="4x4",
                command=self.on_press_board_size,
                variable=board_size,
                value=4),
            'AC3': Radiobutton(
                algorithm_frame,
                text="Constraint Propagation (AC-3)",
                variable=algorithm,
                command=(lambda: self.update_algorithm_checkbuttons('AC3')),
                # Value needs to be an int type, not an IntEnum. Otherwise, .get() will not work.
                value=AlgorithmTypes.AC3.value),
            'BacktrackingSearch': Radiobutton(
                algorithm_frame,
                text="Backtracking Search",
                variable=algorithm,
                command=(lambda: self.update_algorithm_checkbuttons('BacktrackingSearch')),
                value=AlgorithmTypes.BACKTRACKING_SEARCH.value)
        }
        algorithm_options = {}
        algorithm_options_list = [
            ('MRV', "Minimum-remaining-values heuristic"),
            ('Degree', "Degree heuristic"),
            ('LCV', "Least-constraining-value heuristic"),
            ('ForwardChecking', "Forward checking")
        ]
        for key, description in algorithm_options_list:
            algorithm_options[key] = IntVar()
            options[key] = Checkbutton(
                algorithm_options_frame,
                text=description,
                command=(lambda button=key: self.update_algorithm_checkbuttons(button)),
                variable=algorithm_options[key]
            )
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

    def on_press_board_size(self):
        # Call function in SudokuCSPSolver
        self.change_board_size_fn(self.board_size.get())

    def get_algorithm_value(self) -> int:
        return self.algorithm.get()

    def update_algorithm_checkbuttons(self, button: str) -> None:
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
                self.options[option].state(['disabled'])
        elif button == 'BacktrackingSearch':
            # Enable algorithm options
            for option in algorithm_options:
                self.options[option].state(['!disabled'])
        elif button == 'MRV':
            if self.algorithm_options['MRV'].get() == 0:
                # If MRV heuristic is unchecked, make sure Degree heuristic is also unchecked.
                self.algorithm_options['Degree'].set(0)
            else:
                # If MRV heuristic is checked, make sure that forward checking is also checked.
                self.algorithm_options['ForwardChecking'].set(1)
        elif button == 'Degree':
            if self.algorithm_options['Degree'].get() == 1:
                # If Degree heuristic is checked, make sure MRV heuristic and forward checking are also checked.
                self.algorithm_options['MRV'].set(1)
                self.algorithm_options['ForwardChecking'].set(1)
        elif button == 'ForwardChecking':
            if self.algorithm_options['ForwardChecking'].get() == 0:
                # If forward checking is unchecked, make sure that MRV heuristic and Degree heuristic are also
                # unchecked.
                self.algorithm_options['MRV'].set(0)
                self.algorithm_options['Degree'].set(0)

    def is_algorithm_option_selected(self, option) -> bool:
        return self.algorithm_options[option].get() == 1


class StepControlButtons(Enum):
    FIRST = auto()
    PREVIOUS = auto()
    NEXT = auto()
    LAST = auto()


class InfoPanelSectionTypes(Enum):
    none = auto()
    AC3 = auto()
    BACKTRACKING = auto()


class InfoPanelSectionsAC3(Enum):
    MESSAGE = auto()
    CURRENT_ARC = auto()
    CURRENT_QUEUE = auto()


class InfoPanelSectionsBacktracking(Enum):
    MESSAGE = auto()
    CURRENT_ASSIGNMENT = auto()
    CURRENT_VARIABLE = auto()
    ORDERED_VALUES = auto()
    CURRENT_VALUE = auto()


class InfoPanelView(Frame):
    def __init__(self, go_to_step_fn, master=None, **kw):
        super().__init__(master, **kw)
        # A reference to the function is passed in so that it can easily reference objects out of the current class's
        # scope.
        self.go_to_step_fn = go_to_step_fn
        # Don't automatically associate the value with the widget but set it manually, as users may enter invalid info.
        self.current_step = 1
        self.current_step_entry, self.total_steps, self.step_controls, self.sections, self.images = self.make_gui()
        # Keep track of which section should be visible (none by default)
        self.visible_section = InfoPanelSectionTypes.none
        self.change_section(InfoPanelSectionTypes.none)

    def make_gui(self) -> (Entry, Label, dict, dict, dict):
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
        Label(self, text="Information", font="TkHeadingFont 16").pack()
        # Step #/#
        step_frame = Frame(self)
        step_frame.pack()
        step_info_frame = Frame(self)
        step_info_frame.pack(anchor=W)
        Label(step_info_frame, text="Step: ").pack(side=LEFT)
        current_step_entry = Entry(step_info_frame, width=4, justify=RIGHT)
        current_step_entry.pack(side=LEFT)

        # We create a function variable instead of just using a lambda, as .bind() passes in the event as the argument
        def onEnter():
            self.go_to_step_fn(self.current_step_entry.get())
        current_step_entry.bind(
            '<Return>',
            (lambda event: onEnter())
        )
        Label(step_info_frame, text="/").pack(side=LEFT)
        total_steps = Label(step_info_frame)
        total_steps.pack(side=LEFT)
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
        # TODO: Make the scrolled text box resize with window
        queue_text = ScrolledText(queue_frame, width=text_box_width)
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
        # TODO: Make the scrolled text box resize with window
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
        self.current_step = step
        self.current_step_entry.delete('0', END)
        self.current_step_entry.insert(INSERT, str(step))

    def set_total_steps(self, num_steps: int) -> None:
        self.total_steps.configure(text=str(num_steps))

    def go_to_first_step(self) -> None:
        self.go_to_step_fn('1')

    def go_to_previous_step(self) -> None:
        self.go_to_step_fn(str(self.current_step - 1))

    def go_to_next_step(self) -> None:
        self.go_to_step_fn(str(self.current_step + 1))

    def go_to_last_step(self) -> None:
        self.go_to_step_fn(self.total_steps.cget('text'))

    def set_step_controls(self):
        # Make sure that controls are set correctly
        total_steps = int(self.total_steps.cget('text'))
        if total_steps <= 1:
            self.step_controls[StepControlButtons.FIRST].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.PREVIOUS].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.NEXT].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.LAST].state(['disabled', '!focus'])
        elif self.current_step == 1:
            self.step_controls[StepControlButtons.FIRST].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.PREVIOUS].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.NEXT].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.LAST].state(['!disabled', '!focus'])
        elif self.current_step == total_steps:
            self.step_controls[StepControlButtons.FIRST].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.PREVIOUS].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.NEXT].state(['disabled', '!focus'])
            self.step_controls[StepControlButtons.LAST].state(['disabled', '!focus'])
        else:
            self.step_controls[StepControlButtons.FIRST].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.PREVIOUS].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.NEXT].state(['!disabled', '!focus'])
            self.step_controls[StepControlButtons.LAST].state(['!disabled', '!focus'])

    def set_section(self, section, obj) -> None:
        if self.visible_section is InfoPanelSectionTypes.AC3:
            if section is InfoPanelSectionsAC3.MESSAGE:
                obj_string = obj if obj is not None else ""
                self.sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsAC3.CURRENT_ARC:
                obj_string = "{}, {}".format(obj[0], obj[1]) if obj is not None and len(obj) == 2 else ""
                self.sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsAC3.CURRENT_QUEUE:
                obj_string = ""
                if obj is not None:
                    obj_list = ["{}, {}".format(i[0], i[1]) for i in list(obj)]
                    obj_string = '\n'.join(obj_list)
                # Need to enable to set text
                self.sections[section].configure(state=NORMAL)
                # First line, first character to end of text
                self.sections[section].delete('1.0', END)
                self.sections[section].insert(INSERT, obj_string)
                self.sections[section].configure(state=DISABLED)
            else:
                raise ValueError("No behavior defined for given section")
        elif self.visible_section is InfoPanelSectionTypes.BACKTRACKING:
            if section is InfoPanelSectionsBacktracking.MESSAGE:
                obj_string = obj if obj is not None else ""
                self.sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.CURRENT_ASSIGNMENT:
                obj_string = ""
                if obj is not None:
                    # We sort the result so it's easier for a human to read
                    obj_list = ["'{}'={}".format(var_name, obj[var_name]) for var_name in sorted(obj.keys())]
                    obj_string = '\n'.join(obj_list)
                # Need to enable to set text
                self.sections[section].configure(state=NORMAL)
                # First line, first character to end of text
                self.sections[section].delete('1.0', END)
                self.sections[section].insert(INSERT, obj_string)
                self.sections[section].configure(state=DISABLED)
            elif section is InfoPanelSectionsBacktracking.CURRENT_VARIABLE:
                obj_string = obj if obj is not None else ""
                self.sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.ORDERED_VALUES:
                obj_string = ""
                if obj is not None:
                    obj_list = [str(i) for i in obj]
                    obj_string = ', '.join(obj_list)
                self.sections[section].configure(text=obj_string)
            elif section is InfoPanelSectionsBacktracking.CURRENT_VALUE:
                obj_string = str(obj) if obj is not None else ""
                self.sections[section].configure(text=obj_string)

    def reset_panel(self) -> None:
        self.current_step = 1
        self.current_step_entry.delete('0', END)
        self.set_total_steps(0)
        self.set_step_controls()
        if self.visible_section is InfoPanelSectionTypes.AC3:
            for section in InfoPanelSectionsAC3:
                self.set_section(section, None)
        elif self.visible_section is InfoPanelSectionTypes.BACKTRACKING:
            for section in InfoPanelSectionsBacktracking:
                self.set_section(section, None)
        else:
            pass

    def change_section(self, section: InfoPanelSectionTypes) -> None:
        self.visible_section = section
        if section is InfoPanelSectionTypes.AC3:
            self.sections[InfoPanelSectionTypes.BACKTRACKING].pack_forget()
            self.sections[InfoPanelSectionTypes.AC3].pack()
        elif section is InfoPanelSectionTypes.BACKTRACKING:
            self.sections[InfoPanelSectionTypes.AC3].pack_forget()
            self.sections[InfoPanelSectionTypes.BACKTRACKING].pack()
        else:
            self.sections[InfoPanelSectionTypes.AC3].pack_forget()
            self.sections[InfoPanelSectionTypes.BACKTRACKING].pack_forget()


class SudokuCSPSolver:
    def __init__(self):
        self.board_size = 9
        if len(sys.argv) == 2:
            if len(sys.argv[1]) == 4*4:
                self.board_size = 4
            elif len(sys.argv[1]) == 9*9:
                self.board_size = 9
            else:
                raise ValueError("The initial puzzle string has an invalid length.")
        self.root, self.board_views, self.main_panel, self.message, self.buttons = self.make_gui()
        initial_board = str(self.board_size)+'_'+AppMode.INPUT.name
        self.board_view = self.board_views[initial_board]
        # Hide the board(s) that are not active
        for view in self.board_views:
            if view != initial_board:
                self.board_views[view].grid_remove()
        # Only show the options panel
        for panel in self.main_panel:
            if type(self.main_panel[panel]) is not OptionsPanelView:
                self.main_panel[panel].grid_remove()
        self.entry_disabled = False
        # Fill out cells with initial values if applicable
        if len(sys.argv) == 2:
            self.board_view.set_board(values=sys.argv[1], entry_disabled=self.entry_disabled)
        # Store the current puzzle
        self.puzzle = None
        # Store history of solver
        self.history = None
        self.selected_algorithm = None
        # Keep CSP after it's generated to be able to access its properties from methods other than solve()
        self.csp = None

    def run(self) -> None:
        self.root.mainloop()

    def make_gui(self) -> tuple:
        """Create the tk GUI."""
        # Set dimensions for the two main panels of the application, to allow showing/hiding widgets without changing
        # the size of the window.
        board_frame_height = 500
        board_frame_width = 500
        panel_frame_width = 350

        root = Tk()

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
        message_bar.pack()
        message = Label(message_bar)
        message.pack(side=LEFT, expand=YES, fill=BOTH)
        # Toolbar
        toolbar = Frame(root)
        toolbar.pack(pady=10)
        buttons = {
            'solve_button': Button(toolbar, text="Solve", command=self.solve),
            'reset_button': Button(toolbar, text="Reset solver", command=self.reset),
            'clear_button': Button(toolbar, text="Clear all cells", command=self.clear)
        }
        # ttk buttons have more complex states than can be handled by the .configure command
        buttons['reset_button'].state(['disabled'])
        buttons['solve_button'].pack(side=LEFT, padx=5)
        buttons['reset_button'].pack(side=LEFT, padx=5)
        buttons['clear_button'].pack(side=LEFT, padx=5)
        root.title("Sudoku CSP Solver")
        return root, board_views, main_panel, message, buttons

    def solve(self) -> None:
        """Solve the Sudoku puzzle."""
        # widget.after() to handle long-running process
        # Remove any existing messages
        self.reset_message()
        # Make sure options are valid
        if not self.validate_options():
            return
        # Read cells and create Sudoku board
        puzzle_as_list = self.board_view.get_board()
        # Save off board. We don't use SudokuBoard.to_list() as it depends on a valid puzzle.
        self.puzzle = puzzle_as_list
        # Create the Sudoku
        board = SudokuBoard(size=self.board_size)
        try:
            board.set_cells(puzzle_as_list)
        except ValueError:
            self.set_message(text="There are duplicate values in a row, column, or region.", error=True)
            return
        self.set_controls(AppMode.SOLVE)
        # Change to solver view
        self.change_board_type(AppMode.SOLVE)
        # self.board_view.set_initial_board(puzzle_as_list)
        # Change to information panel
        self.change_panel(InfoPanelView)
        # Solve using selected options
        self.selected_algorithm = AlgorithmTypes(self.main_panel['options_panel'].get_algorithm_value())
        # Change information panel's section to match the algorithm
        if self.selected_algorithm is AlgorithmTypes.AC3:
            section_type = InfoPanelSectionTypes.AC3
        elif self.selected_algorithm is AlgorithmTypes.BACKTRACKING_SEARCH:
            section_type = InfoPanelSectionTypes.BACKTRACKING
        else:
            section_type = InfoPanelSectionTypes.none
        self.main_panel['info_panel'].change_section(section_type)
        self.csp = board.generate_csp()
        if self.selected_algorithm == AlgorithmTypes.AC3:
            algorithm_runner = AC3(self.csp, record_history=True)
        elif self.selected_algorithm == AlgorithmTypes.BACKTRACKING_SEARCH:
            suv_heuristic = SelectUnassignedVariableHeuristics.none
            odv_heuristic = OrderDomainValuesHeuristics.none
            inference_fn = InferenceFunctions.none
            if self.main_panel['options_panel'].is_algorithm_option_selected('MRV'):
                suv_heuristic = SelectUnassignedVariableHeuristics.MRV
            if self.main_panel['options_panel'].is_algorithm_option_selected('Degree'):
                suv_heuristic = SelectUnassignedVariableHeuristics.DegreeHeuristic
            if self.main_panel['options_panel'].is_algorithm_option_selected('LCV'):
                odv_heuristic = OrderDomainValuesHeuristics.LCV
            if self.main_panel['options_panel'].is_algorithm_option_selected('ForwardChecking'):
                inference_fn = InferenceFunctions.ForwardChecking
            algorithm_runner = BacktrackingSearch(
                csp=self.csp,
                select_unassigned_variable_heuristic=suv_heuristic,
                order_domain_values_heuristic=odv_heuristic,
                inference_function=inference_fn,
                record_history=True
            )
        else:
            raise ValueError("Invalid value for algorithm")
        result = algorithm_runner.run()
        # Both AC3 and backtracking search can return no consistent assignment
        if result is None:
            self.set_message(text="The search algorithm could not find a consistent assignment.", error=True)
        elif self.selected_algorithm is AlgorithmTypes.AC3:
            # AC3 can return a partial assignment
            partial_assignment = False
            for variable_name in result.keys():
                if len(result[variable_name]) > 1:
                    partial_assignment = True
                    break
            if partial_assignment:
                self.set_message(text="AC3 algorithm returned a partial assignment.", error=True)
        # Set values in GUI
        # result_string = self.result_dict_to_string(result)
        # self.board_view.set_board(values=result_string, entry_disabled=self.entry_disabled)
        # Store history in instance so it will be accessible to other methods
        self.history = algorithm_runner.history
        num_steps = len(self.history)
        self.main_panel['info_panel'].set_total_steps(num_steps)
        # Set first step in history
        self.main_panel['info_panel'].go_to_first_step()

    @staticmethod
    def puzzle_list_to_string(puzzle: list):
        # Turn integers to strings if necessary
        temp_list = [str(puzzle[i]) for i in range(len(puzzle))]
        puzzle_string = ''.join(temp_list)
        return puzzle_string

    @staticmethod
    def result_dict_to_string(result: dict) -> str:
        """Convert a result dictionary to a string for easy parsing."""
        result_list = []
        for var_name in sorted(result):
            digit = result[var_name][0] if type(result[var_name]) is list else result[var_name]
            result_list.append(str(digit))
        result_string = ''.join(result_list)
        return result_string

    def reset(self) -> None:
        """Reset Sudoku board from solved state to original state."""
        # Remove any existing messages
        self.reset_message()
        self.board_view.reset_board(self.puzzle)
        self.set_controls(AppMode.INPUT)
        self.change_board_type(AppMode.INPUT)
        self.main_panel['info_panel'].reset_panel()
        self.change_panel(OptionsPanelView)

    def clear(self) -> None:
        """Clear all cells in the Sudoku puzzle."""
        # Remove any existing messages
        self.reset_message()
        self.board_view.clear_board()

    def reset_message(self) -> None:
        """Reset the message UI element."""
        self.message.configure(foreground='black', text="")

    def set_message(self, text: str, error: bool = False) -> None:
        """Set the message UI element."""
        color = 'red' if error else 'black'
        self.message.configure(foreground=color, text=text)

    def change_board_size(self, size: int):
        # Hide current board
        self.board_view.grid_remove()
        # Show new board
        self.board_size = size
        self.board_view = self.board_views[str(self.board_size)+'_'+AppMode.INPUT.name]
        self.board_view.grid()

    def set_controls(self, mode: AppMode):
        if mode == AppMode.SOLVE:
            self.entry_disabled = True
            # for row in self.board_view.entries:
            #     for entry in row:
            #         entry.configure(state=DISABLED)
            # Need to remove keyboard focus when disabling button being pressed
            self.buttons['solve_button'].state(['disabled', '!focus'])
            self.buttons['reset_button'].state(['!disabled'])
            self.buttons['clear_button'].state(['disabled'])
        else:
            self.entry_disabled = False
            self.buttons['solve_button'].state(['!disabled'])
            self.buttons['reset_button'].state(['disabled', '!focus'])
            self.buttons['clear_button'].state(['!disabled'])

    def change_board_type(self, mode: AppMode):
        # Hide current board
        self.board_view.grid_remove()
        # Show new board
        self.board_view = self.board_views["{}_{}".format(str(self.board_size), mode.name)]
        self.board_view.grid()

    def change_panel(self, panel_type: type):
        for panel in self.main_panel:
            if type(self.main_panel[panel]) is not panel_type:
                self.main_panel[panel].grid_remove()
            else:
                self.main_panel[panel].grid()

    def go_to_step(self, step_string: str) -> None:
        # Clear message first
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
        self.main_panel['info_panel'].set_current_step(step)
        self.main_panel['info_panel'].set_step_controls()
        if self.selected_algorithm is AlgorithmTypes.AC3:
            # Set board
            self.board_view.highlight_current_variables(history_step[AC3HistoryItems.CURRENT_ARC])
            self.board_view.set_domains(history_step[AC3HistoryItems.DOMAINS])
            # Change all necessary widgets to reflect info in new step
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.MESSAGE,
                history_step[AC3HistoryItems.MESSAGE]
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.CURRENT_ARC,
                history_step[AC3HistoryItems.CURRENT_ARC]
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsAC3.CURRENT_QUEUE,
                history_step[AC3HistoryItems.CURRENT_QUEUE]
            )
        elif self.selected_algorithm is AlgorithmTypes.BACKTRACKING_SEARCH:
            # Set board
            # Clear any previous highlighted values
            self.board_view.clear_all_highlighted_values()
            current_variable = history_step[BacktrackingSearchHistoryItems.CURRENT_VARIABLE]
            if current_variable is not None:
                highlight_variables = [current_variable]
            else:
                # Pass in an empty list to deselect all variables
                highlight_variables = []
            self.board_view.highlight_current_variables(highlight_variables)
            current_value = history_step[BacktrackingSearchHistoryItems.CURRENT_VALUE]
            if current_value is not None:
                self.board_view.highlight_value_in_variable(current_variable, current_value, highlight_type=1)
            # Set assignment after current value so that when the current value gets assigned to the variable, it will
            # be highlighted as an assignment.
            assignment = history_step[BacktrackingSearchHistoryItems.CURRENT_ASSIGNMENT]
            for variable in assignment.keys():
                self.board_view.highlight_value_in_variable(variable, assignment[variable], highlight_type=2)
            domains = history_step[BacktrackingSearchHistoryItems.INFERENCES]
            if domains is None:
                # Show all values if there's no inferencing
                domains = self.csp.get_all_domains()
            self.board_view.set_domains(domains)
            # Change all necessary widgets to reflect info in new step
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.MESSAGE,
                history_step[BacktrackingSearchHistoryItems.MESSAGE]
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_ASSIGNMENT,
                assignment
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_VARIABLE,
                current_variable
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.ORDERED_VALUES,
                history_step[BacktrackingSearchHistoryItems.ORDERED_VALUES]
            )
            self.main_panel['info_panel'].set_section(
                InfoPanelSectionsBacktracking.CURRENT_VALUE,
                current_value
            )
        else:
            raise ValueError("No defined behavior for selected_algorithm value")

    def validate_options(self) -> bool:
        # Use the raw Enum value so we can check if it's not in AlgorithmTypes
        selected_algorithm = self.main_panel['options_panel'].get_algorithm_value()
        if selected_algorithm != AlgorithmTypes.AC3 and selected_algorithm != AlgorithmTypes.BACKTRACKING_SEARCH:
            self.set_message("No algorithm selected", error=True)
            return False
        if self.board_size == 9 and selected_algorithm == AlgorithmTypes.BACKTRACKING_SEARCH and \
                not self.main_panel['options_panel'].is_algorithm_option_selected('MRV'):
            self.set_message("Minimum-remaining-values heuristic must be selected for backtracking search when the " +
                             "board size is 9x9", error=True)
            return False
        return True


def main():
    solver = SudokuCSPSolver()
    solver.run()


if __name__ == "__main__":
    main()
