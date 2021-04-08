import java.io.BufferedWriter;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.Socket;

public class ServerSender extends Thread {

    private Socket socketConnection;
    private OutputStream outputStream;
    private OutputStreamWriter outputStreamWriter;
    private BufferedWriter bufferedWriter;

    public ServerSender(Socket socketConnection) {
        this.socketConnection = socketConnection;

        try {
            outputStream = socketConnection.getOutputStream();
            outputStreamWriter = new OutputStreamWriter(outputStream);
            bufferedWriter = new BufferedWriter(outputStreamWriter);
        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ServerSender - "+e);
        }

    }

    public void run(String menssage) {

        try {

            bufferedWriter.write(menssage);
            bufferedWriter.flush();

        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("ServerReciver run - "+e);
        }

    }
}
