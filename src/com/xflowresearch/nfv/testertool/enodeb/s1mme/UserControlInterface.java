package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.SocketException;
import java.net.UnknownHostException;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.AttachSimulator;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;

public class UserControlInterface
{
	public void listenForUserControlCommands(XMLParser xmlparser, eNodeB enodeb, SctpClient sctpClient)
	{
		new Thread()
		{
			public void run()
			{
				DatagramSocket serverSocket = null;
				try
				{
					serverSocket = new DatagramSocket(9877, InetAddress.getByName("10.20.30.8"));
					//serverSocket = new ServerSocket(9877, 20, InetAddress.);
				}
				catch(SocketException e)
				{
					e.printStackTrace();
				}
				catch(UnknownHostException e)
				{
					// TODO Auto-generated catch block
					e.printStackTrace();
				}

				byte [] buffer = new byte[2048];
				

				// Create a packet to receive data into the buffer
				DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

				while(true)
				{
					// Wait to receive a datagram
					try
					{
						serverSocket.receive(packet);
					}
					catch(IOException e)
					{
						e.printStackTrace();
					}

					// Convert the contents to a string, and display them
					byte [] data = new byte[packet.getLength()];
					System.arraycopy(packet.getData(), packet.getOffset(), data, 0, packet.getLength());
					packet.setLength(buffer.length);
					
					String stringData = new String(data);
					
					InetAddress IPAddress = packet.getAddress();
					int port = packet.getPort();
					// make new thread UserCommandHandler
					
					UserCommandHandler uch = new UserCommandHandler(stringData, serverSocket, enodeb, xmlparser, IPAddress, port, sctpClient);
					new Thread(uch).start();
					// Reset the length of the packet before reusing it.
					
				}

			}// public void run..

		}.start(); // new Thread..
	}


}
