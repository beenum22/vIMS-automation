package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

import com.xflowresearch.nfv.testertool.enodeb.eNodeB;

public class UserDataInterface
{

	int i = 0;

	private InetAddress transportLayerAddress;

	private DatagramSocket serverSocket = null;

	private DatagramSocket socket = null;

	public void setTransportLayerAddress(InetAddress transportLayerAddress)
	{
		this.transportLayerAddress = transportLayerAddress;
	}

	public void listenForUserDataTraffic(eNodeB enodeb)
	{
		new Thread()
		{
			public void run()
			{
				try
				{
					serverSocket = new DatagramSocket(9876);
				}
				
				catch (SocketException e)
				{
					e.printStackTrace();
				}

				byte[] buffer = new byte[2048];

				// Create a packet to receive data into the buffer
				DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

				while(true)
				{
					// Wait to receive a datagram
					try
					{
						serverSocket.receive(packet);
					}

					catch (IOException e)
					{
						e.printStackTrace();
					}

					// Convert the contents to a string, and display them
					byte[] data = new byte[packet.getLength()];
					System.arraycopy(packet.getData(), packet.getOffset(), data, 0, packet.getLength());

					String stringData = bytesToHex(data);

					System.out.println("Data Received:" + stringData);

					// simulateGTPEchoRequest(enodeb);
					handleUserData(stringData, enodeb);

					// Reset the length of the packet before reusing it.
					packet.setLength(buffer.length);
				}
			}// public void run..
		}.start(); // new Thread..
	}

	/// GTP
	/// Echo////////////////////////////////////////////////////////////////////////

	public void simulateGTPEchoRequest(eNodeB enodeb)
	{
		System.out.println("Sending GTP Echo");
		User user = enodeb.getUser(0);

		////////////// GTP Echo Packet Creation Here////////////////////
		GTPacket gtpacket = new GTPacket("001", 1, 0, 0, 0, 0);
		gtpacket.setMessageType("01");
		gtpacket.setLength(0);
		gtpacket.setTEID(user.getTEID());

		byte[] byteGTPacket = gtpacket.getPacket();

		sendGTPacketToSGW(byteGTPacket);
		////////////// GTP Echo Packet Creation Here////////////////////
	}
	/// GTP
	/// Echo////////////////////////////////////////////////////////////////////////

	/** Received User Data, Apply GTP Tunnel and send to S-GW **/
	public void handleUserData(String ipPdu, eNodeB enodeb)
	{
		User user = enodeb.getUser(0);

		GTPacket gtpacket = new GTPacket("001", 1, 0, 0, 0, 0);
		gtpacket.setMessageType("ff");
		gtpacket.setLength(ipPdu.length() / 2);
		gtpacket.setTEID(user.getTEID());
		gtpacket.setTPDU(ipPdu);

		byte[] byteGTPacket = gtpacket.getPacket();

		sendGTPacketToSGW(byteGTPacket);
	}

	public void sendGTPacketToSGW(byte[] byteGTPacket)
	{
		/**
		 * Send and Receive the Response from the GTP Message Asynchronously
		 **/
		new Thread()
		{
			public void run()
			{

				if(socket == null)
				{
					try
					{
						socket = new DatagramSocket(2152);
					}
					
					catch (SocketException e)
					{
						e.printStackTrace();
					}
				}

				DatagramPacket packet = new DatagramPacket(byteGTPacket, byteGTPacket.length, transportLayerAddress,
						2152);
				try
				{
					socket.send(packet);
				}
				
				catch (IOException e)
				{
					e.printStackTrace();
				}

				byte[] receiveData = new byte[1024];
				DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
				
				try
				{
					socket.receive(receivePacket);
				}
				
				catch (IOException e)
				{
					e.printStackTrace();
				}

				byte[] data = new byte[receivePacket.getLength()];
				System.arraycopy(receivePacket.getData(), receivePacket.getOffset(), data, 0,
						receivePacket.getLength());

				String stringData = bytesToHex(data);
				System.out.println("Data Recieved From S-GW:" + stringData);

				/////////////////// Remove the GTP Tunnel
				/////////////////// Here///////////////////////////
				String untunneled = stringData.substring(16, stringData.length());
				System.out.println("Untunneled From S-GW:" + untunneled);
				data = hexStringToByteArray(untunneled);
				/////////////////// Remove the GTP Tunnel
				/////////////////// Here///////////////////////////

				// send data to the sniffer
				try
				{
					DatagramPacket packet1 = new DatagramPacket(data, data.length, InetAddress.getByName("127.0.0.1"),
							9999);
					serverSocket.send(packet1);
				}
				
				catch (IOException e)
				{
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				// send data to the sniffer

				receivePacket.setLength(receiveData.length);
			}
		}.start();
	}

	/**
	 * Convert byte array to hex String
	 */
	final protected static char[] hexArray = "0123456789ABCDEF".toCharArray();

	public static String bytesToHex(byte[] bytes)
	{
		char[] hexChars = new char[bytes.length * 2];
		for (int j = 0; j < bytes.length; j++)
		{
			int v = bytes[j] & 0xFF;
			hexChars[j * 2] = hexArray[v >>> 4];
			hexChars[j * 2 + 1] = hexArray[v & 0x0F];
		}
		return new String(hexChars);
	}

	public static byte[] hexStringToByteArray(String s)
	{
		byte[] b = new byte[s.length() / 2];
		for (int i = 0; i < b.length; i++)
		{
			int index = i * 2;
			int v = Integer.parseInt(s.substring(index, index + 2), 16);
			b[i] = (byte) v;
		}
		return b;
	}
}
