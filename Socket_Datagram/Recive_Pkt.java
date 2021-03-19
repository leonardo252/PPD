import java.net.DatagramPacket;
import java.net.DatagramSocket;

public class Recive_Pkt {
    public static void main(String[] args) {

        // Definindo a porta
        int porta = 1024;

        // Definindo o buffer de recepçâo
        byte[] buffer = new byte[1000];

        try {
            // Cria o socket
            DatagramSocket socket = new DatagramSocket(porta);

            // Criar o pacote para receber os dados
            DatagramPacket pacote = new DatagramPacket(buffer, buffer.length);

            // Laço para receber e mostrar o conteudo
            while(true) {
                socket.receive(pacote);

                String conteudo  = new String(pacote.getData(), 0, pacote.getLength());
                
                System.out.println("End. de Origem: " + pacote.getAddress());
                System.out.println("Conteudo do pacote: " + conteudo + "\n");

                // Redefinir o tamanho do pacote
                pacote.setLength(buffer.length);
            }

        } catch (Exception e) {

        }
    }
}