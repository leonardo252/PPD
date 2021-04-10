import java.io.IOException;
import java.net.Socket;
import java.net.UnknownHostException;

public class Client {

    private static Socket socketConnection;

    public ClientReciver reciver;
    public ClientSender sender;

    private Integer socketPort = 1024;
    private String socketIP = "127.0.0.1";

    public static void main(String[] args) {

        Client client = new Client();
        socketConnection = client.conect();

//        for (int i = 0; i < 5; i++) {
//            System.out.println(i);
//            client.sendMenssage("Menssagem "+i+"\r\n");
//        }

//        client.starRecive();
        client.sendMenssage("Menssagem Client \r\n");

    }

    public Client() {

        System.out.println("Starting Client");

    }

    public Socket conect() {
        try {
            Socket connection = new Socket(socketIP, socketPort);
            return connection;

        } catch (UnknownHostException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    public void starRecive() {

        reciver = new ClientReciver(socketConnection);
        reciver.run();
    }

    public void sendMenssage(String menssage) {

        sender = new ClientSender(socketConnection);
        sender.run(menssage);

    }


}
