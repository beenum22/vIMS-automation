package testing;


import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

import com.sun.nio.sctp.MessageInfo;
import com.sun.nio.sctp.SctpChannel;
import com.xflowresearch.nfv.s1ap.S1APDefinitions;
import com.xflowresearch.nfv.testertool.sctp.SctpClient;

/**
 * @author ahmad
 * 
 */
//Class for Testing. . .  

public class Testing
{
	public static void main(String [] args) throws InterruptedException
	{
		SctpClient client = new SctpClient();
		client.connectToHost("127.0.0.1", 1111);


		String value = "000005000800020001001a001a1907417108091132547698214305e0e000000000050202d011d1004300060010f1321011006440124010f13201388010000000010004ac1101280086400130";

		int valueLength = value.length()/2;
		System.out.println("-"+valueLength+"<><><>"+Integer.toHexString(valueLength));

		String s1apPacket =  (S1APDefinitions.Type.InitiatingMessage.getHexCode()+
				S1APDefinitions.ProcedureCode.initialUEMessage.getHexCode()+ 
				S1APDefinitions.Criticality.ignore.getHexCode()+
				Integer.toHexString(valueLength)+
				value);

		byte [] message = hexStringToByteArray(s1apPacket);
		client.sendProtocolPayload(message, 18);
		Thread.sleep(2000);
		client.disconnectFromHost();

	}







	public void aMethod() throws IOException {
		try {

			InetAddress address = InetAddress.getByName("127.0.0.1");
			SocketAddress socketAddress = new InetSocketAddress(address, 1111);
			System.out.println("open connection for socket [" + socketAddress + "]");

			SctpChannel sctpChannel = SctpChannel.open();
			sctpChannel.bind(new InetSocketAddress(6060));

			sctpChannel.connect(socketAddress, 1 ,1);

			System.out.println("sctpChannel.getRemoteAddresses() = " + sctpChannel.getRemoteAddresses());
			System.out.println("sctpChannel.getAllLocalAddresses() = " + sctpChannel.getAllLocalAddresses());
			System.out.println("sctpChannel.isConnectionPending() = " + sctpChannel.isConnectionPending());
			System.out.println("sctpChannel.isOpen() = " + sctpChannel.isOpen());
			System.out.println("sctpChannel.isRegistered() = " + sctpChannel.isRegistered());
			System.out.println("sctpChannel.provider() = " + sctpChannel.provider());
			System.out.println("sctpChannel.association() = " + sctpChannel.association());

			System.out.println("send bytes");
			final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);

			//  00,0c,40,4c,00,00,05,00,08,00,02,00,01,00,1a,00,1a,19,07,41,71,08,09,11,32,54,76,98,21,43,05,e0,e0,00,00,00,00,05,02,02,d0,11,d1,00,43,00,06,00,10,f1,32,10,11,00,64,40,12,40,10,f1,32,01,38,80,10,00,00,00,01,00,04,ac,11,01,28,00,86,40,01,30,
			//Simple M3ua ASP_Up message
			String data = "000c404c000005000800020001001a001a1907417108091132547698214305e0e000000000050202d011d1004300060010f1321011006440124010f13201388010000000010004ac1101280086400130";
			
			byte [] message = hexStringToByteArray(data);


			final MessageInfo messageInfo = MessageInfo.createOutgoing(null, 0);
			System.out.println("messageInfo = " + messageInfo);
			System.out.println("messageInfo.streamNumber() = " + messageInfo.streamNumber());

			byteBuffer.put(message);
			byteBuffer.flip();

			//////////////////////
			messageInfo.payloadProtocolID(18);
			////////////////////////
			try {
				Thread.sleep(5000);
				sctpChannel.send(byteBuffer, messageInfo);
			} catch (Exception e) {
				e.printStackTrace();
			}
			//Thread.sleep(100000);

			//
			System.out.println("close connection");
			sctpChannel.close();


		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public static byte[] hexStringToByteArray(String s) {
		byte[] b = new byte[s.length() / 2];
		for (int i = 0; i < b.length; i++) {
			int index = i * 2;
			int v = Integer.parseInt(s.substring(index, index + 2), 16);
			b[i] = (byte) v;
		}
		return b;
	}
}