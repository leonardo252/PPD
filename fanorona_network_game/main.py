import tkinter as tk

from ui.main_window import FanoronaNetworkWindow


def main() -> None:
    root = tk.Tk()
    FanoronaNetworkWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
