import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.Socket;

public class ServerReciver extends Thread {

    final private Socket socketConnection;
    private InputStream inputStream;
    private InputStreamReader inputStreamReader;
    private BufferedReader bufferedReader;
    private String menssage;


    // args[0] -> port

    public ServerReciver(Socket socketConnection) {
        this.socketConnection = socketConnection;
        try {
            inputStream = socketConnection.getInputStream();
            inputStreamReader = new InputStreamReader(inputStream);
            bufferedReader = new BufferedReader(inputStreamReader);
        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ServerReciver - "+e);
        }
    }

    @Override
    public void run() {

        try {
            menssage = bufferedReader.readLine();

            while(menssage != null) {

                System.out.println(menssage);
                menssage = bufferedReader.readLine();

            }
//            socketConnection.close();


        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ServerReciver run - "+e);
        }

    }

    public String getMenssage() {
        return menssage;
    }
}
