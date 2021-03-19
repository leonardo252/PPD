package Socket_Datagram;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Scanner;

public class Send_Pkt {
    public static void main(String[] args) {
        try {
            // Definindo IP e porta de destino
            InetAddress servidor = InetAddress.getByName("localhost");
            int porta = 1024;

            // Criando Socket
            DatagramSocket socket = new DatagramSocket();

            // Laço para ler linhas do teclado
            Scanner input = new Scanner(System.in);
            String linha = input.nextLine();

            while(!linha.equals(".")) {
                // Cria o pacote com os dados da linha
                byte[] dados = linha.getBytes();
                DatagramPacket pacote = new DatagramPacket(dados, dados.length, servidor, porta);

                // Envia o pacote ao endereço de destino
                socket.send(pacote);
                
                // Lê  a próxima linha
                linha = input.nextLine();
            }
        
        } catch (Exception e) {
            System.out.println(e);
        }
    }
}