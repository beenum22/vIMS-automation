package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.SocketException;

public class UserControlInterface {
	
	public void listenForUserControlCommands()
	{
		new Thread()
		{
			public void run()
			{
				DatagramSocket serverSocket = null;

				try 
				{
					serverSocket = new DatagramSocket(9877);
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
					
					String stringData = new String(data);
			        
			        // Reset the length of the packet before reusing it.
			        packet.setLength(buffer.length); 
			      }
				
			}//public void run..
			
		}.start();   //new Thread..

	}
	
	public void executeUECommand(String command){
		System.out.println("Command Recieved:"+command);
	}

}
