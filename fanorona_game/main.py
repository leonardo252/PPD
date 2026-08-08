import tkinter as tk

from ui.main_window import FanoronaWindow


def main() -> None:
    root = tk.Tk()
    FanoronaWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
