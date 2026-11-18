import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from client.controller import ClientController
from common.config import (
    DEFAULT_LOCAL_WORKERS,
    MAX_LOCAL_WORKERS,
)
from common.counter import normalize_keywords


class ClientWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Projeto MOM - Cliente Produtor")
        self.root.geometry("830x650")
        self.root.minsize(720, 580)
        self.controller = None
        self.connected = False

        self.file_path = tk.StringVar()
        self.keywords = tk.StringVar(value="python")
        self.worker_count = tk.IntVar(value=DEFAULT_LOCAL_WORKERS)
        self.status = tk.StringVar(value="Conectando automaticamente ao RabbitMQ...")
        self.job = tk.StringVar(value="Nenhum processamento iniciado")
        self.even_count = tk.IntVar(value=0)
        self.odd_count = tk.IntVar(value=0)

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(150, self._connect)

    def _build(self):
        broker = tk.LabelFrame(self.root, text="RabbitMQ", padx=10, pady=10)
        broker.pack(fill="x", padx=14, pady=(14, 7))
        tk.Label(broker, text="Broker local configurado automaticamente", anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        self.connect_button = tk.Button(broker, text="Reconectar", width=12, command=self._connect)
        self.connect_button.grid(row=0, column=1, padx=(12, 0))
        broker.columnconfigure(0, weight=1)
        tk.Label(broker, textvariable=self.status, anchor="w", fg="#14532d").grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        task = tk.LabelFrame(self.root, text="Processamento", padx=10, pady=10)
        task.pack(fill="x", padx=14, pady=7)
        task.columnconfigure(1, weight=1)
        tk.Label(task, text="Arquivo:").grid(row=0, column=0, sticky="e")
        tk.Entry(task, textvariable=self.file_path).grid(row=0, column=1, sticky="ew", padx=6)
        tk.Button(task, text="Selecionar", command=self._select_file).grid(row=0, column=2)
        tk.Label(task, text="Palavras-chave:").grid(row=1, column=0, sticky="e", pady=(8, 0))
        tk.Entry(task, textvariable=self.keywords).grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=(8, 0)
        )
        tk.Label(task, text="Workers locais:").grid(row=2, column=0, sticky="e", pady=(8, 0))
        self.worker_spin = tk.Spinbox(
            task, from_=0, to=MAX_LOCAL_WORKERS, textvariable=self.worker_count, width=6
        )
        self.worker_spin.grid(row=2, column=1, sticky="w", padx=6, pady=(8, 0))
        tk.Label(task, text="0 permite usar somente workers externos.", fg="#555555").grid(
            row=2, column=1, columnspan=2, sticky="w", padx=(65, 0), pady=(8, 0)
        )
        self.start_button = tk.Button(
            task, text="Iniciar processamento", state="disabled", command=self._start_job
        )
        self.start_button.grid(row=3, column=0, columnspan=3, pady=(12, 0))

        progress = tk.LabelFrame(self.root, text="Leitores produtores", padx=10, pady=10)
        progress.pack(fill="x", padx=14, pady=7)
        tk.Label(progress, text="Leitor de linhas pares:").grid(row=0, column=0, sticky="e")
        tk.Label(progress, textvariable=self.even_count, width=12, anchor="w").grid(row=0, column=1)
        tk.Label(progress, text="Leitor de linhas impares:").grid(row=1, column=0, sticky="e")
        tk.Label(progress, textvariable=self.odd_count, width=12, anchor="w").grid(row=1, column=1)
        tk.Label(progress, textvariable=self.job, anchor="w", font=("Arial", 11, "bold")).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0)
        )

        log_frame = tk.LabelFrame(self.root, text="Operacoes MOM", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True, padx=14, pady=(7, 14))
        self.log = scrolledtext.ScrolledText(log_frame, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo de entrada",
            filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")),
        )
        if path:
            self.file_path.set(path)

    def _connect(self):
        self.connect_button.configure(state="disabled")
        self.status.set("Conectando automaticamente ao RabbitMQ...")

        def worker():
            try:
                controller = ClientController()
                controller.connect()
                self.root.after(0, self._connected, controller)
            except Exception as error:
                self.root.after(0, self._connection_failed, error)

        threading.Thread(target=worker, daemon=True).start()

    def _connected(self, controller):
        self.controller = controller
        self.connected = True
        self.status.set("Conectado ao RabbitMQ local")
        self.start_button.configure(state="normal")
        self._append_log("Conexao STOMP estabelecida. Fila e topico prontos.")

    def _connection_failed(self, error):
        self.status.set("RabbitMQ indisponivel. Inicie o servico e tente novamente: {}".format(error))
        self.connect_button.configure(state="normal")

    def _start_job(self):
        path = self.file_path.get().strip()
        keywords = normalize_keywords(self.keywords.get())
        if not path:
            messagebox.showerror("Arquivo", "Selecione o arquivo de entrada.")
            return
        if not keywords:
            messagebox.showerror("Palavras-chave", "Informe pelo menos uma palavra-chave.")
            return
        try:
            count = int(self.worker_count.get())
            if not 0 <= count <= MAX_LOCAL_WORKERS:
                raise ValueError
        except ValueError:
            messagebox.showerror("Workers", "Quantidade de workers invalida.")
            return

        self.start_button.configure(state="disabled")
        self.worker_spin.configure(state="disabled")
        self.controller.on_progress = self._reader_progress_from_thread
        self.controller.on_finished = self._readers_finished_from_thread

        def worker():
            try:
                if count:
                    self.controller.start_local_workers(count)
                job_id = self.controller.start_job(path, keywords)
                self.root.after(0, self._job_started, job_id, count)
            except Exception as error:
                self.root.after(0, self._job_failed, error)

        threading.Thread(target=worker, daemon=True).start()

    def _job_started(self, job_id, workers):
        self.job.set("Job: {} | {} worker(s) local(is)".format(job_id[:12], workers))
        self._append_log("job_started publicado no topico.")
        self._append_log("Dois leitores iniciados: pares e impares.")

    def _job_failed(self, error):
        self._append_log("Falha: {}".format(error))
        self.start_button.configure(state="normal")

    def _reader_progress_from_thread(self, name, count):
        self.root.after(0, self._reader_progress, name, count)

    def _reader_progress(self, name, count):
        target = self.even_count if name == "leitor-pares" else self.odd_count
        target.set(count)

    def _readers_finished_from_thread(self, even, odd, errors):
        self.root.after(0, self._readers_finished, even, odd, errors)

    def _readers_finished(self, even, odd, errors):
        self.even_count.set(even)
        self.odd_count.set(odd)
        if errors:
            self._append_log("Leitura encerrada com erro: {}".format(errors[0]))
            return
        self._append_log("job_manifest publicado: {} linhas.".format(even + odd))
        self.status.set("Todas as linhas foram publicadas na fila")

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _close(self):
        if self.controller:
            try:
                self.controller.close()
            except Exception:
                pass
        self.root.destroy()
