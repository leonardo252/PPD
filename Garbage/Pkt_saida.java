import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.InterfaceAddress;
import java.io.*;
import java.net.*;

public class Pkt_saida {

    public static void main(String[] args) {
        try {
            // Definindo os dados do pacote de saida
            String out = "Hello Socket!";
            byte[] data_out = out.getBytes();

            // Define o IP e a porta de destino
            InetAddress ip = InetAddress.getByName("ifce.edu.br");
            int porta = 7;

            // Cria o pacote com dados IP e porta
            DatagramPacket pacote = new DatagramPacket(data_out, data_out.length, ip, porta);

            // Mostra os dados do pacote
            System.out.println(new String(pacote.getData(), "ASCII"));
        } catch (Exception e) {
            System.out.println(e);
        }
    }

}