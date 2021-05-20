import javax.swing.*;
import java.rmi.*;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class OtheloServer extends UnicastRemoteObject implements OtheloInterface {

    private static MainScreen frame;
    OtheloInterface client;

    public OtheloServer() throws RemoteException {
        super();
        System.out.println("Serviço criado!");

        frame = new MainScreen("Othelo");
        frame.setVisible(true);

        frame.enviarButton.addActionListener(e -> {
            try {
                frame.upChat(frame.userName +": " + frame.menssagemTextField.getText());
                client.sendMenssage(frame.userName +": " + frame.menssagemTextField.getText());
                frame.menssagemTextField.setText("");
            } catch (RemoteException remoteException) {
                remoteException.printStackTrace();
            }
        });


    }

    public static void toSend(String msg) {
        System.out.println("Foi o nome menino, enviado."+ msg);
    }

    public void sendMenssage(String msg) throws RemoteException {
        frame.upChat(msg);
        System.out.println(msg);
    }
}
