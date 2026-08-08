from __future__ import annotations

import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from typing import Optional

from network.connection import StreamingConnection


class MainWindow:
    DEFAULT_PORT = 5000

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        self.connection: Optional[StreamingConnection] = None
        self.server_socket: Optional[socket.socket] = None

        self.is_waiting_for_client = False

        self.mode_variable = tk.StringVar(value="server")
        self.host_variable = tk.StringVar(value="127.0.0.1")
        self.port_variable = tk.StringVar(value=str(self.DEFAULT_PORT))
        self.status_variable = tk.StringVar(value="Desconectado")

        self._configure_window()
        self._build_interface()
        self._update_mode_fields()

        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _configure_window(self) -> None:
        self.root.title("Fanorona - Comunicação")

        self.root.geometry("760x560")
        self.root.minsize(650, 500)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _build_interface(self) -> None:
        self._build_connection_frame()
        self._build_chat_frame()
        self._build_status_bar()

    def _build_connection_frame(self) -> None:
        connection_frame = tk.LabelFrame(
            self.root,
            text="Configuração da conexão",
            padx=12,
            pady=12,
        )
        connection_frame.grid(
            row=0,
            column=0,
            padx=16,
            pady=(16, 8),
            sticky="ew",
        )

        connection_frame.columnconfigure(3, weight=1)

        server_radio = tk.Radiobutton(
            connection_frame,
            text="Servidor",
            variable=self.mode_variable,
            value="server",
            command=self._update_mode_fields,
        )
        server_radio.grid(
            row=0,
            column=0,
            padx=(0, 12),
            sticky="w",
        )

        client_radio = tk.Radiobutton(
            connection_frame,
            text="Cliente",
            variable=self.mode_variable,
            value="client",
            command=self._update_mode_fields,
        )
        client_radio.grid(
            row=0,
            column=1,
            padx=(0, 20),
            sticky="w",
        )

        host_label = tk.Label(
            connection_frame,
            text="IP do servidor:",
        )
        host_label.grid(
            row=0,
            column=2,
            padx=(0, 6),
            sticky="e",
        )

        self.host_entry = tk.Entry(
            connection_frame,
            textvariable=self.host_variable,
            width=18,
        )
        self.host_entry.grid(
            row=0,
            column=3,
            padx=(0, 12),
            sticky="ew",
        )

        port_label = tk.Label(
            connection_frame,
            text="Porta:",
        )
        port_label.grid(
            row=0,
            column=4,
            padx=(0, 6),
            sticky="e",
        )

        self.port_entry = tk.Entry(
            connection_frame,
            textvariable=self.port_variable,
            width=8,
        )
        self.port_entry.grid(
            row=0,
            column=5,
            padx=(0, 12),
        )

        self.connect_button = tk.Button(
            connection_frame,
            text="Iniciar servidor",
            width=16,
            command=self._handle_connection_button,
        )
        self.connect_button.grid(
            row=0,
            column=6,
        )

    def _build_chat_frame(self) -> None:
        chat_frame = tk.LabelFrame(
            self.root,
            text="Mensagens",
            padx=12,
            pady=12,
        )
        chat_frame.grid(
            row=1,
            column=0,
            padx=16,
            pady=8,
            sticky="nsew",
        )

        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        self.chat_history = scrolledtext.ScrolledText(
            chat_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Arial", 12),
        )
        self.chat_history.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="nsew",
        )

        self.message_entry = tk.Entry(
            chat_frame,
            font=("Arial", 12),
            state=tk.DISABLED,
        )
        self.message_entry.grid(
            row=1,
            column=0,
            padx=(0, 8),
            pady=(12, 0),
            sticky="ew",
        )

        self.message_entry.bind(
            "<Return>",
            self._handle_enter_key,
        )

        self.send_button = tk.Button(
            chat_frame,
            text="Enviar",
            width=12,
            state=tk.DISABLED,
            command=self._send_message,
        )
        self.send_button.grid(
            row=1,
            column=1,
            pady=(12, 0),
        )

    def _build_status_bar(self) -> None:
        status_frame = tk.Frame(
            self.root,
            bd=1,
            relief=tk.SUNKEN,
        )
        status_frame.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        status_label = tk.Label(
            status_frame,
            textvariable=self.status_variable,
            anchor="w",
            padx=10,
            pady=6,
        )
        status_label.pack(
            fill=tk.X,
        )

    def _update_mode_fields(self) -> None:
        if self._has_active_connection():
            return

        mode = self.mode_variable.get()

        if mode == "server":
            self.host_entry.configure(state=tk.DISABLED)
            self.connect_button.configure(
                text="Iniciar servidor",
            )
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.connect_button.configure(
                text="Conectar",
            )

    def _handle_connection_button(self) -> None:
        if self._has_active_connection() or self.is_waiting_for_client:
            self._disconnect()
            return

        try:
            port = self._get_port()
        except ValueError as error:
            messagebox.showerror(
                "Porta inválida",
                str(error),
            )
            return

        mode = self.mode_variable.get()

        self._set_configuration_enabled(False)
        self.connect_button.configure(
            text="Desconectar",
            state=tk.NORMAL,
        )

        if mode == "server":
            self._start_server(port)
        else:
            host = self.host_variable.get().strip()

            if not host:
                messagebox.showerror(
                    "IP inválido",
                    "Informe o IP do servidor.",
                )
                self._restore_disconnected_interface()
                return

            self._connect_as_client(host, port)

    def _get_port(self) -> int:
        port_text = self.port_variable.get().strip()

        try:
            port = int(port_text)
        except ValueError:
            raise ValueError("A porta precisa ser um número inteiro.")

        if port < 1 or port > 65535:
            raise ValueError(
                "A porta deve estar entre 1 e 65535."
            )

        return port

    def _start_server(self, port: int) -> None:
        self.is_waiting_for_client = True
        self.status_variable.set(
            "Iniciando servidor..."
        )

        server_thread = threading.Thread(
            target=self._server_worker,
            args=(port,),
            daemon=True,
        )
        server_thread.start()

    def _server_worker(self, port: int) -> None:
        server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        try:
            server_socket.bind(
                ("0.0.0.0", port)
            )
            server_socket.listen(1)

            self.server_socket = server_socket

            local_ip = self._get_local_ip()

            self.root.after(
                0,
                lambda: self.status_variable.set(
                    "Servidor aguardando conexão em "
                    "{}:{}".format(local_ip, port)
                ),
            )

            self.root.after(
                0,
                lambda: self._append_system_message(
                    "Servidor iniciado em {}:{}.".format(
                        local_ip,
                        port,
                    )
                ),
            )

            self.root.after(
                0,
                lambda: self._append_system_message(
                    "Aguardando conexão do cliente..."
                ),
            )

            connection_socket, address = server_socket.accept()

            if not self.is_waiting_for_client:
                connection_socket.close()
                return

            self.root.after(
                0,
                lambda: self._handle_connected_socket(
                    connection_socket,
                    "Cliente conectado: {}:{}".format(
                        address[0],
                        address[1],
                    ),
                ),
            )

        except OSError as error:
            if self.is_waiting_for_client:
                self.root.after(
                    0,
                    lambda error=error: self._handle_connection_error(
                        "Não foi possível iniciar o servidor:\n{}".format(
                            error
                        )
                    ),
                )

        finally:
            self.is_waiting_for_client = False

            try:
                server_socket.close()
            except OSError:
                pass

            self.server_socket = None

    def _connect_as_client(
        self,
        host: str,
        port: int,
    ) -> None:
        self.status_variable.set(
            "Conectando a {}:{}...".format(
                host,
                port,
            )
        )

        client_thread = threading.Thread(
            target=self._client_worker,
            args=(host, port),
            daemon=True,
        )
        client_thread.start()

    def _client_worker(
        self,
        host: str,
        port: int,
    ) -> None:
        client_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        client_socket.settimeout(10)

        try:
            client_socket.connect(
                (host, port)
            )

            client_socket.settimeout(None)

            self.root.after(
                0,
                lambda: self._handle_connected_socket(
                    client_socket,
                    "Conectado ao servidor {}:{}.".format(
                        host,
                        port,
                    ),
                ),
            )

        except OSError as error:
            try:
                client_socket.close()
            except OSError:
                pass

            self.root.after(
                0,
                lambda error=error: self._handle_connection_error(
                    "Não foi possível conectar:\n{}".format(
                        error
                    )
                ),
            )

    def _handle_connected_socket(
        self,
        connection_socket: socket.socket,
        message: str,
    ) -> None:
        self.is_waiting_for_client = False

        self.connection = StreamingConnection(
            connection_socket
        )

        self.connection.on_message = self._on_message_received
        self.connection.on_disconnect = self._on_connection_closed

        self.connection.start_receiving()

        self.status_variable.set("Conectado")
        self.connect_button.configure(
            text="Desconectar",
        )

        self.message_entry.configure(
            state=tk.NORMAL,
        )
        self.send_button.configure(
            state=tk.NORMAL,
        )

        self.message_entry.focus_set()

        self._append_system_message(message)
        self._append_system_message(
            "A comunicação está aberta."
        )

    def _send_message(self) -> None:
        message = self.message_entry.get().strip()

        if not message:
            return

        if self.connection is None:
            messagebox.showwarning(
                "Sem conexão",
                "Não existe uma conexão ativa.",
            )
            return

        sent = self.connection.send(message)

        if not sent:
            messagebox.showerror(
                "Erro",
                "Não foi possível enviar a mensagem.",
            )
            return

        self._append_message(
            sender="Você",
            message=message,
        )

        self.message_entry.delete(
            0,
            tk.END,
        )

    def _handle_enter_key(self, event: object) -> str:
        self._send_message()
        return "break"

    def _on_message_received(self, message: str) -> None:
        """
        Este callback é executado pela thread de rede.

        Tkinter só pode ser alterado pela thread principal,
        portanto usamos root.after.
        """
        self.root.after(
            0,
            lambda: self._append_message(
                sender="Outro jogador",
                message=message,
            ),
        )

    def _on_connection_closed(self) -> None:
        self.root.after(
            0,
            self._handle_disconnection_from_remote,
        )

    def _handle_disconnection_from_remote(self) -> None:
        self.connection = None

        self._append_system_message(
            "O outro participante encerrou a conexão."
        )

        self._restore_disconnected_interface()

    def _disconnect(self) -> None:
        self.is_waiting_for_client = False

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

            self.server_socket = None

        if self.connection is not None:
            current_connection = self.connection
            self.connection = None
            current_connection.close()

        self._append_system_message(
            "Conexão encerrada."
        )

        self._restore_disconnected_interface()

    def _restore_disconnected_interface(self) -> None:
        self.status_variable.set("Desconectado")

        self.message_entry.configure(
            state=tk.DISABLED,
        )
        self.send_button.configure(
            state=tk.DISABLED,
        )

        self._set_configuration_enabled(True)
        self._update_mode_fields()

    def _handle_connection_error(
        self,
        message: str,
    ) -> None:
        self.is_waiting_for_client = False

        messagebox.showerror(
            "Erro de conexão",
            message,
        )

        self._append_system_message(message)
        self._restore_disconnected_interface()

    def _set_configuration_enabled(
        self,
        enabled: bool,
    ) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED

        self.port_entry.configure(state=state)

        for child in self.root.winfo_children():
            self._set_radio_button_state(
                child,
                state,
            )

        if enabled:
            self.connect_button.configure(
                state=tk.NORMAL,
            )
        else:
            self.host_entry.configure(
                state=tk.DISABLED,
            )

    def _set_radio_button_state(
        self,
        widget: tk.Widget,
        state: str,
    ) -> None:
        if isinstance(widget, tk.Radiobutton):
            widget.configure(state=state)

        for child in widget.winfo_children():
            self._set_radio_button_state(
                child,
                state,
            )

    def _append_message(
        self,
        sender: str,
        message: str,
    ) -> None:
        self.chat_history.configure(
            state=tk.NORMAL,
        )

        self.chat_history.insert(
            tk.END,
            "{}: {}\n".format(
                sender,
                message,
            ),
        )

        self.chat_history.configure(
            state=tk.DISABLED,
        )

        self.chat_history.see(tk.END)

    def _append_system_message(
        self,
        message: str,
    ) -> None:
        self.chat_history.configure(
            state=tk.NORMAL,
        )

        self.chat_history.insert(
            tk.END,
            "[Sistema] {}\n".format(message),
        )

        self.chat_history.configure(
            state=tk.DISABLED,
        )

        self.chat_history.see(tk.END)

    def _get_local_ip(self) -> str:
        temporary_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            temporary_socket.connect(
                ("8.8.8.8", 80)
            )
            return temporary_socket.getsockname()[0]

        except OSError:
            return "127.0.0.1"

        finally:
            temporary_socket.close()

    def _has_active_connection(self) -> bool:
        return (
            self.connection is not None
            and self.connection.is_connected
        )

    def _on_window_close(self) -> None:
        self.is_waiting_for_client = False

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

        if self.connection is not None:
            self.connection.close()

        self.root.destroy()