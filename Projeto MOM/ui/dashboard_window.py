import queue
import threading
import tkinter as tk
from tkinter import ttk

from dashboard.state import DashboardState
from dashboard.subscriber import DashboardSubscriber


class DashboardWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Projeto MOM - Dashboard")
        self.root.geometry("900x660")
        self.root.minsize(760, 580)
        self.subscriber = None
        self.state = DashboardState()

        self.connection_status = tk.StringVar(value="Conectando automaticamente ao RabbitMQ...")
        self.job_label = tk.StringVar(value="Aguardando job_started")
        self.file_label = tk.StringVar(value="Arquivo: -")
        self.lines_label = tk.StringVar(value="Linhas: 0 / ?")
        self.workers_label = tk.StringVar(value="Workers ativos: 0")
        self.time_label = tk.StringVar(value="Tempo: 0,00 s")
        self.status_label = tk.StringVar(value="Estado: aguardando")
        self.progress_value = tk.DoubleVar(value=0.0)

        self._build()
        self.root.after(100, self._drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(150, self._connect)

    def _build(self):
        broker = tk.LabelFrame(self.root, text="Subscriber do topico RabbitMQ", padx=10, pady=10)
        broker.pack(fill="x", padx=14, pady=(14, 7))
        tk.Label(broker, text="Broker local configurado automaticamente", anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        self.connect_button = tk.Button(broker, text="Reconectar", command=self._connect)
        self.connect_button.grid(row=0, column=1, padx=(12, 0))
        broker.columnconfigure(0, weight=1)
        tk.Label(broker, textvariable=self.connection_status, anchor="w", fg="#14532d").grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        summary = tk.LabelFrame(self.root, text="Processamento atual", padx=12, pady=10)
        summary.pack(fill="x", padx=14, pady=7)
        tk.Label(summary, textvariable=self.job_label, font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.file_label, anchor="w").pack(fill="x", pady=(4, 0))
        info = tk.Frame(summary)
        info.pack(fill="x", pady=(7, 4))
        tk.Label(info, textvariable=self.lines_label).pack(side="left")
        tk.Label(info, textvariable=self.workers_label).pack(side="left", padx=20)
        tk.Label(info, textvariable=self.time_label).pack(side="left")
        tk.Label(info, textvariable=self.status_label).pack(side="right")
        ttk.Progressbar(summary, variable=self.progress_value, maximum=100).pack(fill="x", pady=(5, 0))

        counts = tk.LabelFrame(self.root, text="Contagem de palavras-chave", padx=8, pady=8)
        counts.pack(fill="both", expand=True, padx=14, pady=7)
        self.tree = ttk.Treeview(counts, columns=("keyword", "count"), show="headings")
        self.tree.heading("keyword", text="Palavra-chave")
        self.tree.heading("count", text="Quantidade")
        self.tree.column("keyword", width=480, anchor="w")
        self.tree.column("count", width=150, anchor="center")
        self.tree.pack(fill="both", expand=True)

        workers = tk.LabelFrame(self.root, text="Workers que processaram linhas", padx=8, pady=8)
        workers.pack(fill="x", padx=14, pady=(7, 14))
        self.worker_list = tk.Label(workers, text="Nenhum resultado recebido", anchor="w", justify="left")
        self.worker_list.pack(fill="x")

    def _connect(self):
        self.connect_button.configure(state="disabled")
        self.connection_status.set("Conectando automaticamente ao RabbitMQ...")

        def worker():
            try:
                subscriber = DashboardSubscriber()
                subscriber.connect()
                self.root.after(0, self._connected, subscriber)
            except Exception as error:
                self.root.after(0, self._connection_failed, error)

        threading.Thread(target=worker, daemon=True).start()

    def _connected(self, subscriber):
        self.subscriber = subscriber
        self.connection_status.set("Conectado e inscrito em /topic/mom.keyword.results")

    def _connection_failed(self, error):
        self.connection_status.set("RabbitMQ indisponivel. Inicie o servico: {}".format(error))
        self.connect_button.configure(state="normal")

    def _drain_events(self):
        if self.subscriber:
            while True:
                try:
                    event_type, value = self.subscriber.events.get_nowait()
                except queue.Empty:
                    break
                if event_type == "message":
                    if self.state.apply(value):
                        self._refresh()
                elif event_type == "error":
                    self.connection_status.set("Erro do broker: {}".format(value))
                elif event_type == "disconnected":
                    self.connection_status.set(value)
        self.root.after(100, self._drain_events)

    def _refresh(self):
        state = self.state.active_job
        self.workers_label.set("Workers ativos: {}".format(len(self.state.active_workers)))
        if state is None:
            return
        self.job_label.set("Job: {}".format(state.job_id))
        self.file_label.set("Arquivo: {}".format(state.file_name or "aguardando manifesto"))
        total = "?" if state.total_lines is None else str(state.total_lines)
        self.lines_label.set("Linhas: {} / {}".format(state.processed_count, total))
        self.time_label.set("Tempo: {:.2f} s".format(state.elapsed).replace(".", ","))
        self.progress_value.set(state.progress)
        self.status_label.set("Estado: concluido" if state.complete else "Estado: processando")

        for item in self.tree.get_children():
            self.tree.delete(item)
        for keyword in state.keywords:
            self.tree.insert("", "end", values=(keyword, state.totals.get(keyword, 0)))
        workers = sorted(state.workers_seen)
        self.worker_list.configure(text=", ".join(workers) if workers else "Nenhum resultado recebido")

    def _close(self):
        if self.subscriber:
            try:
                self.subscriber.disconnect()
            except Exception:
                pass
        self.root.destroy()
