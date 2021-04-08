import javax.swing.*;
import java.awt.*;

public class MainScreen extends JFrame {

    private JPanel mainPanel;
    private JTextArea chatTextArea;
    private JTextField menssagemTextField;
    private JTextField textField2;
    private JButton começarButton;
    private JButton desistirButton;
    private JButton enviarButton;
    private JPanel gameArea;
    private JButton button1A;
    private JButton button1B;
    private JButton button1C;
    private JButton button6C;
    private JButton button5C;
    private JButton button4C;
    private JButton button4B;
    private JButton button1H;
    private JButton button1D;
    private JButton button1G;
    private JButton button1F;
    private JButton button1E;
    private JButton button2A;
    private JButton button3A;
    private JButton button2B;
    private JButton button3B;
    private JButton button2C;
    private JButton button3C;
    private JButton button2D;
    private JButton button3D;
    private JButton button2E;
    private JButton button3E;
    private JButton button2F;
    private JButton button3F;
    private JButton button2G;
    private JButton button3G;
    private JButton button2H;
    private JButton button3H;
    private JButton button4H;
    private JButton button4G;
    private JButton button4F;
    private JButton button4E;
    private JButton button4D;
    private JButton button5D;
    private JButton button5B;
    private JButton button6B;
    private JButton button4A;
    private JButton button5E;
    private JButton button5F;
    private JButton button5G;
    private JButton button5H;
    private JButton button6H;
    private JButton button6G;
    private JButton button6F;
    private JButton button6E;
    private JButton button6D;
    private JButton button5A;
    private JButton button6A;
    private JButton button7A;
    private JButton button7B;
    private JButton button7C;
    private JButton button7D;
    private JButton button7E;
    private JButton button7F;
    private JButton button7G;
    private JButton button7H;
    private JButton button8H;
    private JButton button8G;
    private JButton button8F;
    private JButton button8E;
    private JButton button8D;
    private JButton button8C;
    private JButton button8B;
    private JButton button8A;

    public MainScreen(String title) {
        super(title);

        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setContentPane(mainPanel);
        this.pack();
    }

    public static void main(String[] args) {

        JFrame frame = new MainScreen("Othelo");
        frame.setVisible(true);
    }
}
