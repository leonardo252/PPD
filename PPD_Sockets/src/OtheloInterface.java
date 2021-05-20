import java.rmi.Remote;
import java.rmi.RemoteException;

public interface OtheloInterface extends Remote {

    void sendMenssage(String msg) throws  RemoteException;

}
