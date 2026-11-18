import tkinter as tk

from ui.dashboard_window import DashboardWindow


def main():
    root = tk.Tk()
    DashboardWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
