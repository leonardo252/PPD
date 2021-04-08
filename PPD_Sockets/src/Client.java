import java.io.IOException;
import java.net.Socket;
import java.net.UnknownHostException;

public class Client {

    private Socket socketConnection;

    private Integer socketPort = 1024;
    private String socketIP = "127.0.0.1";

    public static void main(String[] args) {

        Client client = new Client();
        Socket connection = client.conect();

        client.starRecive(connection);

//        for (int i = 0; i < 5; i++) {
//            System.out.println(i);
//            client.sendMenssage(connection, "Menssagem "+i+"\r\n");
//        }


    }

    public Client() {

        System.out.println("Starting Client");

    }

    public Socket conect() {
        try {
            socketConnection = new Socket(socketIP, socketPort);
            return socketConnection;

        } catch (UnknownHostException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    public void starRecive(Socket socketCon) {

        ClientReciver reciver = new ClientReciver(socketCon);
        reciver.run();

    }

    public void sendMenssage(Socket socketCon, String menssage) {

        ClientSender sender = new ClientSender(socketCon);
        sender.run(menssage);

    }


}
