package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.SocketException;

public class UserDataInterface 
{

	public void listenForUserDataTraffic()
	{
		new Thread()
		{
			public void run()
			{
				DatagramSocket serverSocket = null;

				try 
				{
					serverSocket = new DatagramSocket(9876);
				} 
				catch (SocketException e) {
					e.printStackTrace();
				}

			      byte[] buffer = new byte[2048];

			      // Create a packet to receive data into the buffer
			      DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

				while (true) 
				{
			        // Wait to receive a datagram
					try 
					{
						serverSocket.receive(packet);
					}
					catch (IOException e) {
						e.printStackTrace();
					}

			        // Convert the contents to a string, and display them
					byte[] data = new byte[packet.getLength()];
					System.arraycopy(packet.getData(), packet.getOffset(), data, 0, packet.getLength());
					
					String stringData = bytesToHex(data);
			        
			        System.out.println("Data Recieved:"+ stringData);
			        handleUserData(stringData);
			        
			        // Reset the length of the packet before reusing it.
			        packet.setLength(buffer.length); 
			      }
				
			}//public void run..
			
		}.start();   //new Thread..

	}
	
	
	public void handleUserData(String ipPdu){
		
		
	}




	/**
	 * Convert byte array to hex String
	 */
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
}
