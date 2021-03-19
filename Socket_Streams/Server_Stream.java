package Socket_Streams;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.*;

public class Server_Stream {
    public static void main(String[] args) {
        try {

            int porta = 1024;

            // Cria um ServerSocket escutnado na porta 1024
            ServerSocket server = new ServerSocket(porta);

            byte[] data = new byte[15];

            while(true) {

                Socket cliente = server.accept();

                InputStream input = cliente.getInputStream();

                input.read(data, 0, data.length);

                System.out.println(new String(data, "ASCII"));

                OutputStream output = cliente.getOutputStream();

                byte[] toSend = "Recebido".getBytes();

                output.write(toSend);

            }

        }catch (Exception e) {

        }
    }
}