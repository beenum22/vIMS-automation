package com.xflowresearch.nfv.testertool.ue;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

public class UEControlInterface {

	public void sendControlCommand(String command)
	{
		DatagramSocket clientSocket = null;
		try {
			clientSocket = new DatagramSocket();
		} catch (SocketException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}

		InetAddress IPAddress = null;
		try {
			IPAddress = InetAddress.getByName("10.20.30.3");
		} catch (UnknownHostException e1) {
			e1.printStackTrace();
		}

		byte[] sendData = new byte[1024];

		sendData = command.getBytes();

		DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, IPAddress, 9877);
		try {
			clientSocket.send(sendPacket);
			System.out.println("Message Sent");
		} catch (IOException e) {
			e.printStackTrace();
		}

		/*
		byte[] receiveData = new byte[1024];
		DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
		clientSocket.receive(receivePacket);
		String modifiedSentence = new String(receivePacket.getData());
		System.out.println("FROM SERVER:" + modifiedSentence);
		 */

		clientSocket.close();
	}

}
