package Socket_Streams;

import java.net.*;
import java.io.*;
import java.util.Scanner;

public class Send_Stream {

    
    public static void main(String[] args) {
        try {

            int porta = 1024; 
            InetAddress ip = InetAddress.getByName("localhost");

            Socket socket = new Socket(ip, porta);
            
            OutputStream out = socket.getOutputStream();

            InputStream in = socket.getInputStream();

            byte[] recive = new byte[15];

            String data = "Streaming";
            byte[] toSend = data.getBytes();

            out.write(toSend);
                    
            while(true) {

                in.read(recive);
                System.out.println(new String(recive, "ASCII"));


                Scanner input = new Scanner(System.in);
                String linha = input.nextLine();

                while(!linha.equals(".")) {
                        // Cria o pacote com os dados da linha
                    byte[] dados = linha.getBytes();
                    // Envia o pacote ao endereço de destino
                    out.write(dados);
                    
                    // Lê  a próxima linha
                    linha = input.nextLine();
                }
                
                //System.out.println("leo");
            }

        
        } catch (Exception e) {
            System.out.println(e);
        }
    }
}