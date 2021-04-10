import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;

public class Server {

    private static ServerSocket serverSocket;
    private static Socket socketConnection;
    private InputStream inputStream;
    private OutputStream outputStream;
    public ServerReciver reciver;
    public ServerSender sender;

    private Integer socketPort = 1024;

    public static void main(String[] args) {

//        Server server = new Server();
//        socketConnection = server.connect();
//
//        server.starRecive();
//        server.sendMenssage("Hello Cleint");


    }

    public Server() {
        System.out.println("Starting Server");

        socketConnection = connect();

    }

    public Socket connect() {
        try {

            serverSocket = new ServerSocket(1024);

            System.out.println("Waiting Connection...");
            Socket connection = serverSocket.accept();

            System.out.println("Client connected...");

            return connection;

        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("Server Main - "+e);
        }

        return null;
    }

    public void starRecive() {
        reciver = new ServerReciver(socketConnection);
        reciver.run();
    }

    public void sendMenssage(String menssage) {
        sender = new ServerSender(socketConnection);
        sender.run(menssage);

    }


}
