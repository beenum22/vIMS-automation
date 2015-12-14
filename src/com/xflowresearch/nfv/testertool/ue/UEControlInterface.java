package com.xflowresearch.nfv.testertool.ue;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.nio.charset.Charset;

public class UEControlInterface
{

	public String sendControlCommand(String command, String eNBIP)
	{
		DatagramSocket clientSocket = null;
		
		try
		{
			clientSocket = new DatagramSocket();
		}
		catch(SocketException e2)
		{
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}

		InetAddress IPAddress = null;
		
		try
		{
			IPAddress = InetAddress.getByName(eNBIP);
		}
		
		catch(UnknownHostException e1)
		{
			e1.printStackTrace();
		}

		byte [] sendData = new byte[1024];

		sendData = command.getBytes();

		DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, IPAddress, 9877);
		
		try
		{
			clientSocket.send(sendPacket);
		}
		
		catch(IOException e)
		{
			e.printStackTrace();
		}

		byte [] receiveData = new byte[1024];
		
		DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
		try
		{
			clientSocket.receive(receivePacket);
		}
		
		catch(IOException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		byte [] data = new byte[receivePacket.getLength()];
		System.arraycopy(receivePacket.getData(), receivePacket.getOffset(), data, 0, receivePacket.getLength());
		String pdnipv4 = new String(data);

		clientSocket.close();

		return pdnipv4;
	}
}
