from tkinter import *
from tkinter.ttk import *
# Re-import tkinter's Label so we can use it even when it's overridden by ttk's import
from tkinter import Label as TkLabel
from sudoku_board import SudokuBoard
from algorithms import AC3, BacktrackingSearch


class Cell(Entry):
    def __init__(self, root, max_digit: int):
        super().__init__(
            root,
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


class SudokuBoardView(Frame):
    def __init__(self, board_size: int, master=None, **kw):
        super().__init__(master, **kw)
        self.board_size = board_size
        self.entries, self.images = self.make_gui()

    def make_gui(self) -> tuple:
        """Create the tk GUI elements using grid manager and images of separators."""
        entries = []
        # These need to be instance variables so that mainloop will be able to reference the images when rendering
        images = {
            'c_separator_img': PhotoImage(file="c_separator.png"),
            'h_separator_img': PhotoImage(file="h_separator.png"),
            'v_separator_img': PhotoImage(file="v_separator.png")
        }

        if self.board_size == 9:
            # Manually set position of separators to avoid convoluted logic
            # . _ . _ . _ .. _ . _ . _ .. _ . _ . _ .
            separator_indices = [0, 2, 4, 6, 7, 9, 11, 13, 14, 16, 18, 20]
            # Range is (number of cells) x (cell + separator) + (remaining separator) + (num of extra-thickness separators)
            range_end = self.board_size*2+1+2
        elif self.board_size == 4:
            # board size is 4
            # . _ . _ .. _ . _ .
            separator_indices = [0, 2, 4, 5, 7, 9]
            range_end = self.board_size*2+1+1
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
                        item = Cell(self, self.board_size)
                if in_cell:
                    item.grid(row=row, column=col, sticky=(N, S, E, W))
                    cols.append(item)
                else:
                    item.grid(row=row, column=col)
            if len(cols) > 0:
                entries.append(cols)
        return entries, images

    def set_board(self, values, entry_disabled: bool) -> None:
        """Tk commands to set the board."""
        for row in range(self.board_size):
            for col in range(self.board_size):
                entry = self.entries[row][col]
                # Keep value blank if 0
                if type(values) is str:
                    value = values[row*self.board_size + col] if values[row*self.board_size + col] != '0' else ''
                else:
                    # value is a 1D list of digits
                    value = str(values[row*self.board_size + col]) if values[row*self.board_size + col] != 0 else ''
                # Needs to enabled to set text
                entry.configure(state=NORMAL)
                entry.delete('0', END)
                entry.insert('0', value)
                if entry_disabled:
                    entry.configure(state=DISABLED)

    def reset_board(self, puzzle) -> None:
        """Reset the board UI elements."""
        self.set_board(values=puzzle, entry_disabled=False)

    def clear_board(self) -> None:
        """Clear board UI elements."""
        self.set_board(values='0'*self.board_size*self.board_size, entry_disabled=False)


class OptionsPanelView(Frame):
    def __init__(self, board_size: int, change_board_size_fn, master=None, **kw):
        super().__init__(master, **kw)
        # A reference to the function is passed in so that the function call will not depend on the Tk hierarchy
        self.change_board_size_fn = change_board_size_fn
        self.options, self.board_size = self.make_gui(board_size)

    def make_gui(self, size: int) -> tuple:
        Label(self, text="Options", font="TkHeadingFont 16").pack(side=TOP)
        Label(self, text="Board size:").pack(side=LEFT)
        board_size = IntVar()
        options = {
            '9x9': Radiobutton(
                self,
                text="9x9",
                command=self.on_press_board_size,
                variable=board_size,
                value=9),
            '4x4': Radiobutton(
                self,
                text="4x4",
                command=self.on_press_board_size,
                variable=board_size,
                value=4)
        }
        # Set initial value
        board_size.set(size)
        options['9x9'].pack(side=LEFT)
        options['4x4'].pack(side=LEFT)
        return options, board_size

    def on_press_board_size(self):
        # Call function in SudokuCSPSolver
        self.change_board_size_fn(self.board_size.get())


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
        self.root, self.board_views, self.message, self.buttons = self.make_gui()
        self.board_view = self.board_views[self.board_size]
        # Hide the board(s) that are not active
        for size in self.board_views:
            if size != self.board_size:
                self.board_views[size].grid_remove()
        self.entry_disabled = False
        # Fill out cells with initial values if applicable
        if len(sys.argv) == 2:
            self.board_view.set_board(values=sys.argv[1], entry_disabled=self.entry_disabled)
        # Store the current puzzle
        self.puzzle = None

    def run(self) -> None:
        self.root.mainloop()

    def make_gui(self) -> tuple:
        """Create the tk GUI."""
        root = Tk()

        upper_part = Frame(root)
        upper_part.pack()
        # Draw all boards (4x4 and 9x9), hiding the inactive board later
        # These need to use the grid manager so that the items can be hidden and shown without losing their place.
        board_views = {}
        for size_index in range(len(SudokuBoard.board_sizes)):
            size = SudokuBoard.board_sizes[size_index]
            board_views[size] = SudokuBoardView(size, upper_part)
            board_views[size].grid(row=0, column=size_index, padx=10, pady=10)
        # Main panel
        main_panel = {
            'options_panel': OptionsPanelView(self.board_size, self.change_board_size, upper_part)
        }
        main_panel['options_panel'].grid(row=0, column=len(SudokuBoard.board_sizes), sticky=N, padx=10, pady=10)

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
        return root, board_views, message, buttons

    def solve(self) -> None:
        """Solve the Sudoku puzzle."""
        # widget.after() to handle long-running process
        # Remove any existing messages
        self.reset_message()
        # Read cells and create Sudoku board
        puzzle_as_list = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                value = self.board_view.entries[row][col].get()
                digit = int(value) if value != '' else 0
                puzzle_as_list.append(digit)
        # Save off board. We don't use SudokuBoard.to_list() as it depends on a valid puzzle.
        self.puzzle = puzzle_as_list
        # Create the Sudoku
        board = SudokuBoard(size=self.board_size)
        try:
            board.set_cells(puzzle_as_list)
        except ValueError:
            self.set_message(text="There are duplicate values in a row, column, or region.", error=True)
            return
        # Disable GUI elements
        self.entry_disabled = True
        for row in self.board_view.entries:
            for entry in row:
                entry.configure(state=DISABLED)
        # Need to remove keyboard focus when disabling button being pressed
        self.buttons['solve_button'].state(['disabled', '!focus'])
        self.buttons['clear_button'].state(['disabled'])
        # Solve using selected options
        ac3_runner = AC3(board.generate_csp())
        result = ac3_runner.run()
        multiple_solutions = False
        for variable_name in result.keys():
            if len(result[variable_name]) > 1:
                multiple_solutions = True
                break
        if multiple_solutions:
            self.set_message(text="There are multiple solutions to this puzzle.", error=True)
            # If there are multiple solutions, keep original puzzle
        else:
            # Set values in GUI
            result_string = self.result_dict_to_string(result)
            self.board_view.set_board(values=result_string, entry_disabled=self.entry_disabled)
        # Allow resetting of puzzle
        self.buttons['reset_button'].state(['!disabled'])

    def result_dict_to_string(self, result: dict) -> str:
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
        self.entry_disabled = False
        self.board_view.reset_board(self.puzzle)
        self.buttons['solve_button'].state(['!disabled'])
        self.buttons['reset_button'].state(['disabled', '!focus'])
        self.buttons['clear_button'].state(['!disabled'])

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
        self.board_view = self.board_views[self.board_size]
        self.board_view.grid()


def main():
    solver = SudokuCSPSolver()
    solver.run()


if __name__ == "__main__":
    main()
