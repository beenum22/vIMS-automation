package com.xflowresearch.nfv.sctpserver;


import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

import com.sun.nio.sctp.MessageInfo;
import com.sun.nio.sctp.SctpChannel;
import com.sun.nio.sctp.SctpServerChannel;

/**
* @author sandarenu
* $LastChangedDate$
* $LastChangedBy$
* $LastChangedRevision$
*/
public class SCTPServer {
	
	private static SctpChannel sctpChannel;

    public static void main(String[] args) throws IOException, InterruptedException {
    	
    	InetAddress address = InetAddress.getByName("127.0.0.1");
        SocketAddress serverSocketAddress = new InetSocketAddress(address, 1111);
        System.out.println("create and bind for sctp address");
        SctpServerChannel sctpServerChannel =  SctpServerChannel.open().bind(serverSocketAddress);
        System.out.println("address bind process finished successfully");

        while ((sctpChannel = sctpServerChannel.accept()) != null) 
        {
            System.out.println("client connection received");
            System.out.println("sctpChannel.getRemoteAddresses() = " + sctpChannel.getRemoteAddresses());
            System.out.println("sctpChannel.association() = " + sctpChannel.association());
          
            final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);
            
            
            for(int i=0;i<=47;i++){
             MessageInfo messageInfo = sctpChannel.receive(byteBuffer , null, null);
             System.out.println(messageInfo);
            }
            
            
          //////////////////////////////////////////////////////////////////////////////////////////////////
         /*   byteBuffer.flip();
            byte[]data = new byte[byteBuffer.remaining()];
            byteBuffer.get(data);
            
            String data1 = bytesToHex(data);
            System.out.println("Data Recieved:");
            System.out.println(data1);
            
            
            Thread.sleep(5000);
            sendMessageToClient("001ac2");
            Thread.sleep(5000);
            sendMessageToClient("a0210c");*/
			
			
            
        }
        
        
    }
    
    public static void sendMessageToClient(String hexMessage){
    	final ByteBuffer byteBuffer1 = ByteBuffer.allocate(64000);
		final MessageInfo messageInfo1 = MessageInfo.createOutgoing(null, 0);
		messageInfo1.payloadProtocolID(18);

		System.out.println("messageInfo = " + messageInfo1);
		System.out.println("messageInfo.streamNumber() = " + messageInfo1.streamNumber());

		byteBuffer1.put(hexStringToByteArray(hexMessage));
		byteBuffer1.flip();

		try {
			sctpChannel.send(byteBuffer1, messageInfo1);
		} catch (Exception e) {
			e.printStackTrace();
		}
    }
    
    
    
    final protected static char[] hexArray = "0123456789ABCDEF".toCharArray();
    public static String bytesToHex(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for ( int j = 0; j < bytes.length; j++ ) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = hexArray[v >>> 4];
            hexChars[j * 2 + 1] = hexArray[v & 0x0F];
        }
        return new String(hexChars);
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