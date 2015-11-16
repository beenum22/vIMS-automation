package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.AttachSimulator;
import com.xflowresearch.nfv.testertool.enodeb.s1u.GTP;

public class UserControlInterface {

	public void listenForUserControlCommands(XMLParser xmlparser, AttachSimulator as)
	{
		new Thread()
		{
			public void run()
			{
				DatagramSocket serverSocket = null;

				try 
				{
					serverSocket = new DatagramSocket(9877, InetAddress.getByName("10.20.30.3"));
				} 
				catch (SocketException e) {
					e.printStackTrace();
				} catch (UnknownHostException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}

				byte[] buffer = new byte[2048];
				byte[] sendData = new byte[1024];

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
					String reply = executeUECommand(stringData, xmlparser, as);

					InetAddress IPAddress = packet.getAddress();
					int port = packet.getPort();
					
					sendData = reply.getBytes();
					DatagramPacket sendPacket =
							new DatagramPacket(sendData, sendData.length, IPAddress, port);
					try {
						serverSocket.send(sendPacket);
					} catch (IOException e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
					}

					// Reset the length of the packet before reusing it.
					packet.setLength(buffer.length);
				}

			}//public void run..

		}.start();   //new Thread..

	}

	public String executeUECommand(String command, XMLParser xmlparser, AttachSimulator as){
		return executeAttachSequence(xmlparser, as);
	}


	public String executeAttachSequence(XMLParser xmlparser, AttachSimulator as)
	{
		/** Test Attach Sequence initiation **/
		GTP gtpEcho = new GTP();

		if(as.initiateAttachSequence(xmlparser))
		{
			return as.getPDNIpv4().toString();
			/**
			 * Simulate HTTP Traffic towards S-GW
			 
			gtpEcho.simulateGTPEchoRequest(as.getTransportLayerAddress(), 
					as.getPDNIpv4(), 
					as.getTEID());
					*/
		}
		return null;
	}

}
