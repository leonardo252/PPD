import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.Socket;

public class ClientReciver extends Thread {

    private Socket socketConnection;
    private InputStream inputStream;
    private InputStreamReader inputStreamReader;
    private BufferedReader bufferedReader;
    private String menssage;

    public ClientReciver(Socket socketConnection) {
        this.socketConnection = socketConnection;

        try {
            inputStream = socketConnection.getInputStream();
            inputStreamReader = new InputStreamReader(inputStream);
            bufferedReader = new BufferedReader(inputStreamReader);
        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ClientReciver - "+e);
        }

    }

    @Override
    public void run() {

        try {

            while (true) {
                if (bufferedReader.ready()) {
                    menssage = bufferedReader.readLine();
                    System.out.println(menssage);
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ClientReciver run - "+e);
        }

    }

    public String getMenssage() { return menssage; }
}
