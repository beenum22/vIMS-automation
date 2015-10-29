package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

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

	}
}
