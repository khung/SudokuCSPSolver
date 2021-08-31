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


class SudokuBoardDisplay:
    def __init__(self):
        # Store the current puzzle
        self.puzzle = [[0 for i in range(9)] for j in range(9)]
        self.root = Tk()
        self.entries = []
        # These need to be instance variables so that mainloop will be able to reference the images when rendering
        self.c_separator_img = PhotoImage(file="c_separator.png")
        self.h_separator_img = PhotoImage(file="h_separator.png")
        self.v_separator_img = PhotoImage(file="v_separator.png")

        # Use grid manager and actual images of separators
        board = Frame(self.root)
        board.pack(expand=YES, fill=BOTH, padx=10, pady=10)
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
                        item = TkLabel(board, image=self.c_separator_img, borderwidth=0)
                    else:
                        # We're at a horizontal separator
                        item = TkLabel(board, image=self.h_separator_img, borderwidth=0)
                else:
                    if col in separator_indices:
                        # We're at a vertical separator
                        item = TkLabel(board, image=self.v_separator_img, borderwidth=0)
                    else:
                        # We're at the cell itself
                        in_cell = True
                        item = Cell(board)
                if in_cell:
                    item.grid(row=row, column=col, sticky=(N, S, E, W))
                    cols.append(item)
                else:
                    item.grid(row=row, column=col)
            if len(cols) > 0:
                self.entries.append(cols)
        # Toolbar
        toolbar = Frame(self.root)
        toolbar.pack(pady=10)
        Button(toolbar, text="Solve", command=self.solve).pack(side=LEFT, padx=5)
        Button(toolbar, text="Reset solver", command=self.reset).pack(side=LEFT, padx=5)
        Button(toolbar, text="Clear all cells", command=self.clear).pack(side=LEFT, padx=5)
        self.root.title("Sudoku CSP Solver")

    def solve(self):
        """Solve the Sudoku puzzle."""
        # widget.after() to handle long-running process
        # Read cells and create Sudoku board
        puzzle = []
        for row in self.entries:
            for entry in row:
                value = entry.get()
                digit = int(value) if value != '' else 0
                puzzle.append(digit)
                # Change GUI elements to read-only
                entry.configure(state=DISABLED)
        # Save off board
        self.puzzle = puzzle
        # Solve using selected options
        board = SudokuBoard(initial_values=puzzle)
        ac3_runner = AC3(board.generate_csp())
        result = ac3_runner.run()
        # Set values in GUI
        for row in range(len(self.entries)):
            for col in range(len(self.entries[row])):
                entry = self.entries[row][col]
                variable_name = str((row+1)*10 + (col+1))
                # Need to re-enable to set text
                entry.configure(state=NORMAL)
                entry.delete('0', END)
                entry.insert('0', str(result[variable_name][0]))
                entry.configure(state=DISABLED)

    def reset(self):
        """Reset Sudoku board from solved state to original state."""
        for row in range(len(self.entries)):
            for col in range(len(self.entries[row])):
                entry = self.entries[row][col]
                digit = self.puzzle[row*9 + col]
                value = str(digit) if digit != 0 else ''
                entry.configure(state=NORMAL)
                entry.delete('0', END)
                entry.insert('0', value)

    def clear(self):
        """Clear all cells in the Sudoku puzzle."""
        for row in range(len(self.entries)):
            for col in range(len(self.entries[row])):
                entry = self.entries[row][col]
                entry.configure(state=NORMAL)
                entry.delete('0', END)


def main():
    display = SudokuBoardDisplay()
    display.root.mainloop()


if __name__ == "__main__":
    main()
