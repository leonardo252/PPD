import tkinter as tk

from ui.client_window import ClientWindow
from ui.dashboard_window import DashboardWindow


def open_client(root):
    root.destroy()
    window = tk.Tk()
    ClientWindow(window)
    window.mainloop()


def open_dashboard(root):
    root.destroy()
    window = tk.Tk()
    DashboardWindow(window)
    window.mainloop()


def main():
    root = tk.Tk()
    root.title("Projeto MOM")
    root.geometry("420x260")
    root.resizable(False, False)
    tk.Label(root, text="Contador de Palavras com MOM", font=("Arial", 16, "bold")).pack(pady=(28, 8))
    tk.Label(root, text="RabbitMQ + STOMP + N workers").pack(pady=(0, 22))
    tk.Button(root, text="Abrir Cliente Produtor", width=28, command=lambda: open_client(root)).pack(pady=6)
    tk.Button(root, text="Abrir Dashboard", width=28, command=lambda: open_dashboard(root)).pack(pady=6)
    tk.Label(root, text="Workers externos: python3 worker_app.py", fg="#555555").pack(pady=(20, 0))
    root.mainloop()


if __name__ == "__main__":
    main()
