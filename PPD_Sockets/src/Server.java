import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;

public class Server {

    private static ServerSocket serverSocket;
    private InputStream inputStream;
    private OutputStream outputStream;

    private Integer socketPort = 1024;

    public static void main(String[] args) {

        try {

            serverSocket = new ServerSocket(1024);

            System.out.println("Waiting Connection...");
            Socket connection = serverSocket.accept();

            System.out.println("Client connected...");
            ServerReciver reciver = new ServerReciver(connection);
            ServerSender sender = new ServerSender(connection);

            reciver.start();

            for (int i = 0; i < 5; i++) {
                System.out.println(i);
                sender.run("Menssagem "+i+"\r\n");
            }

            while (true) {

                if (connection.isClosed() == true) {
                    System.out.println("Connection was closed!");
                    break;
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("Server Main - "+e);
        }


    }

}
