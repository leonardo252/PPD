package Socket_Streams;

import java.net.*;
import java.io.*;

public class Send_Stream {

    
    public static void main(String[] args) {
        try {

            int porta = 1024; 
            InetAddress ip = InetAddress.getByName("localhost");

            Socket socket = new Socket(ip, porta);
            
            OutputStream out = socket.getOutputStream();

            InputStream in = socket.getInputStream();

            byte[] recive = new byte[15];

            while(true) {

                String data = "Streaming";
                byte[] toSend = data.getBytes();

                out.write(toSend);

                in.read(recive);

                System.out.println(new String(recive, "ASCII"));
                //System.out.println("leo");
            }

        
        } catch (Exception e) {
            System.out.println("leo1");
        }
    }
}