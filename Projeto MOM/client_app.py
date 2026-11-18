import tkinter as tk

from ui.client_window import ClientWindow


def main():
    root = tk.Tk()
    ClientWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
