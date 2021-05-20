import java.rmi.*;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class RegisterOthelo {



    public static void main(String args[]) {
        Registry reg;
        try{

            OtheloServer obj = new OtheloServer();

            try {
                reg = LocateRegistry.getRegistry(1099);
                System.out.println(reg.list().length);
                Naming.rebind("//127.0.0.1/OtheloClient",obj);
                OtheloInterface client = (OtheloInterface) Naming.lookup("//127.0.0.1/"+reg.list()[0]);
                obj.client = client;

            } catch (Exception e1) {
                reg = LocateRegistry.createRegistry(1099);
                Naming.rebind("//127.0.0.1/OtheloServer",obj);
                while(reg.list().length != 2);
                OtheloInterface client = (OtheloInterface) Naming.lookup("//127.0.0.1/"+reg.list()[1]);
                obj.client = client;
            }



            System.out.println("Servidor Registrado!");

        } catch (Exception e){System.out.println("Erro" + e);}

    }
}
