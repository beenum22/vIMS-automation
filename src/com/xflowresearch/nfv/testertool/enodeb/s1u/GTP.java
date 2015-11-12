package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;

public class GTP {

	private DatagramSocket socket = null;

	public void simulateGTPEchoRequest(InetAddress transportLayerAddress, InetAddress PDNIpv4, String TEID)
	{
		try 
		{
			socket = new DatagramSocket();
		} 
		catch (SocketException e) {
			e.printStackTrace();
		}

		//////////////GTP Echo Packet Creation Here////////////////////
		GTPacket gtpacket = new GTPacket("001", 1, 0, 0, 0, 0);
		gtpacket.setMessageType("01");
		gtpacket.setLength(0);
		gtpacket.setTEID(TEID);

		byte[] byteGTPacket = gtpacket.getPacket();
		//////////////GTP Echo Packet Creation Here////////////////////


		DatagramPacket packet = new DatagramPacket(byteGTPacket, byteGTPacket.length, transportLayerAddress, 2152);
		try 
		{
			socket.send(packet);
		}
		catch (IOException e) {
			e.printStackTrace();
		}

		
		/** Receive the Response from the GTP Request Asynchronously **/
		new Thread(){
			public void run(){
				byte[] receiveData = new byte[1024];
				DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
				try {
					socket.receive(receivePacket);
				} catch (IOException e) {
					e.printStackTrace();
				}

				String receivedMessage = bytesToHex(receiveData);
				System.out.println("GTP Received:"+receivedMessage);
			}
		}.start();

	}


	public void sendGTPacket(){

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
