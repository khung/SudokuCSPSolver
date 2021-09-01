from tkinter import *
from tkinter.ttk import *
# Re-import tkinter's Label so we can use it even when it's overridden by ttk's import
from tkinter import Label as TkLabel
from sudoku_board import SudokuBoard
from algorithms import AC3, BacktrackingSearch


class Cell(Entry):
    def __init__(self, root):
        super().__init__(
            root,
            width=1,
            font="Helvetica 20",
            justify="center"
        )
        # Only allow 1 digit between 1-9 in entry
        # Validation documentation under http://tcl.tk/man/tcl8.6/TkCmd/entry.htm#M16
        command = (self.register(self.on_validate), "%P")
        self.configure(validate="key", validatecommand=command)

    def on_validate(self, new_value):
        """Validate that the input is a digit between 1 and 9."""
        if new_value == "":
            return True
        try:
            value = int(new_value)
            if 0 < value <= 9:
                return True
            else:
                return False
        except ValueError:
            return False


class SudokuBoardView:
    def __init__(self, root):
        self.entries, self.images = self.make_gui(root)

    def make_gui(self, root) -> tuple:
        """Create the tk GUI."""
        entries = []
        # These need to be instance variables so that mainloop will be able to reference the images when rendering
        images = {
            'c_separator_img': PhotoImage(file="c_separator.png"),
            'h_separator_img': PhotoImage(file="h_separator.png"),
            'v_separator_img': PhotoImage(file="v_separator.png")
        }

        # Manually set position of separators to avoid convoluted logic
        # . _ . _ . _ .. _ . _ . _ .. _ . _ . _ .
        separator_indices = [0, 2, 4, 6, 7, 9, 11, 13, 14, 16, 18, 20]
        # Range is (number of cells) x (cell + separator) + (remaining separator) + (num of extra-thickness separators)
        range_end = 9*2+1+2
        for row in range(0, range_end):
            cols = []
            for col in range(0, range_end):
                in_cell = False
                if row in separator_indices:
                    if col in separator_indices:
                        # We're at a point
                        item = TkLabel(root, image=images['c_separator_img'], borderwidth=0)
                    else:
                        # We're at a horizontal separator
                        item = TkLabel(root, image=images['h_separator_img'], borderwidth=0)
                else:
                    if col in separator_indices:
                        # We're at a vertical separator
                        item = TkLabel(root, image=images['v_separator_img'], borderwidth=0)
                    else:
                        # We're at the cell itself
                        in_cell = True
                        item = Cell(root)
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
        for row in range(len(self.entries)):
            for col in range(len(self.entries[row])):
                entry = self.entries[row][col]
                # Keep value blank if 0
                if type(values) is str:
                    value = values[row * 9 + col] if values[row * 9 + col] != '0' else ''
                else:
                    # value is a 1D list of digits
                    value = str(values[row*9 + col]) if values[row*9 + col] != 0 else ''
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
        self.set_board(values='0'*9*9, entry_disabled=False)


class SudokuCSPSolver:
    def __init__(self):
        self.board_size = 9
        self.root, self.board_view, self.message, self.buttons = self.make_gui()
        self.entry_disabled = False
        self.board = SudokuBoard(size=9)
        # Fill out cells with initial values if applicable
        if len(sys.argv) == 2:
            self.board_view.set_board(values=sys.argv[1], entry_disabled=self.entry_disabled)
        # Store the current puzzle
        self.puzzle = self.board.to_list()

    def run(self):
        self.root.mainloop()

    def make_gui(self) -> tuple:
        """Create the tk GUI."""
        root = Tk()

        # Use grid manager and actual images of separators
        board_frame = Frame(root)
        board_frame.pack(expand=YES, fill=BOTH, padx=10, pady=10)
        board = SudokuBoardView(board_frame)
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
        return root, board, message, buttons

    def solve(self) -> None:
        """Solve the Sudoku puzzle."""
        # widget.after() to handle long-running process
        # Remove any existing messages
        self.reset_message()
        # Read cells and create Sudoku board
        puzzle_as_list = []
        for row in range(9):
            for col in range(9):
                value = self.board_view.entries[row][col].get()
                digit = int(value) if value != '' else 0
                puzzle_as_list.append(digit)
                # Save off board. We don't use SudokuBoard.to_list() as it depends on a valid puzzle.
                self.puzzle[row*9 + col] = digit
        try:
            self.board.set_cells(puzzle_as_list)
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
        ac3_runner = AC3(self.board.generate_csp())
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


def main():
    solver = SudokuCSPSolver()
    solver.run()


if __name__ == "__main__":
    main()
