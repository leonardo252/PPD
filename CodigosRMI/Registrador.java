import java.rmi.*;
import java.rmi.server.*;

public class Registrador {

 public static void main(String args[]) {
try{

   Servidor obj = new Servidor ();

    java.rmi.registry.LocateRegistry.createRegistry(1099); 

   Naming.rebind("//localhost/NewServer",obj);  

   System.out.println("Servidor Registrado!");

  } catch (Exception e){System.out.println("Erro");}
                        
 }
}
