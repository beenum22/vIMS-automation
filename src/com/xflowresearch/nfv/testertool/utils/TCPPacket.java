package com.xflowresearch.nfv.testertool.utils;

import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.util.Random;

import javax.xml.bind.DatatypeConverter;

import org.apache.commons.lang.StringUtils;

public class TCPPacket
{
	private ByteBuffer packetByteBuffer;

	public static String computeChecksum(String packetHex, String srcIP, String dstIP)
	{
		try
		{
			/* Pseudo header for TCP */
			String pseudoHeader = "";

			pseudoHeader += DatatypeConverter.printHexBinary(InetAddress.getByName(srcIP).getAddress());
			pseudoHeader += DatatypeConverter.printHexBinary(InetAddress.getByName(dstIP).getAddress());
			pseudoHeader += "0006";		//1 byte zeros + 1 byte for protocol identifier
			
			String length = StringUtils.leftPad(Integer.toHexString(packetHex.length()/2), 4, "0");
			
			pseudoHeader += length;
			//System.out.println((pseudoHeader+packetHex).length());
			byte [] packetBytes = DatatypeConverter.parseHexBinary(pseudoHeader + packetHex);
			int packetLength = packetBytes.length;
			int i = 0, sum = 0, data = 0;

			while(packetLength > 1)
			{
				data = (packetBytes[i] << 8 & 0xFF00) | (packetBytes[i + 1] & 0xFF); 
				sum += data;

				if((sum & 0xFFFF0000) > 0)
				{
					sum = sum & 0xFFFF;
					sum += 1;
				}

				i += 2;
				packetLength -= 2;
			}

			if(packetLength > 0)
			{
				sum += (packetBytes[i] << 8) & 0xFF00;
				if((sum & 0xFFFF0000) > 0)
				{
					sum = sum & 0xFFFF;
					sum += 1;
				}
			}

			sum = ~sum;
			sum = sum & 0xFFFF;

			String hex = StringUtils.leftPad(Integer.toHexString(sum), 4, "0");
			
			return hex; 
		}

		catch(Exception exc)
		{
			exc.printStackTrace(); 
			return null;
		}
	}

	public TCPPacket(byte [] bytes)
	{
		packetByteBuffer = ByteBuffer.wrap(bytes);
	}

	public static String newTcpSynPacket(String srcIP, String dstIP, int srcPort, int dstPort)
	{
		String hex = "";
		
		hex += StringUtils.leftPad(Integer.toHexString(srcPort), 4, "0");
		hex += StringUtils.leftPad(Integer.toHexString(dstPort), 4, "0");
		
		hex += StringUtils.leftPad(Integer.toHexString(new Random().nextInt()), 8, "0");
		hex += "00000000a002721000000000020405b404020101010101010101010101030307";
//				00000000a002721000000000020405b40402080a001163f00000000001030307
		StringBuilder builder = new StringBuilder(hex);
		builder.replace(32, 36, computeChecksum(hex, srcIP, dstIP));
		
		///return DatatypeConverter.parseHexBinary(builder.toString());
		return builder.toString();
	}
	
	public static String newTcpAckPacket(String srcIP, String dstIP, int srcPort, int dstPort, int sequenceNumber, int ackNumber)
	{
		String hex = "";
		
		hex += StringUtils.leftPad(Integer.toHexString(srcPort), 4, "0");
		hex += StringUtils.leftPad(Integer.toHexString(dstPort), 4, "0");
		
		hex += StringUtils.leftPad(Integer.toHexString(sequenceNumber), 8, "0");
		hex += StringUtils.leftPad(Integer.toHexString(ackNumber), 8, "0");
		hex += "801000ed00000000010101010101010101010101";
//				801000ed000000000101080a00585cdf004a81c5
		StringBuilder builder = new StringBuilder(hex);
		builder.replace(32, 36, computeChecksum(hex, srcIP, dstIP));
		
		//return DatatypeConverter.parseHexBinary(builder.toString());
		return builder.toString();
	}
	
	public static String newTcpFinAckPacket(String srcIP, String dstIP, int srcPort, int dstPort, int sequenceNumber, int ackNumber)
	{
		String hex = "";
		
		hex += StringUtils.leftPad(Integer.toHexString(srcPort), 4, "0");
		hex += StringUtils.leftPad(Integer.toHexString(dstPort), 4, "0");
		
		hex += StringUtils.leftPad(Integer.toHexString(sequenceNumber), 8, "0");
		hex += StringUtils.leftPad(Integer.toHexString(ackNumber), 8, "0");
		hex += "801100ed00000000010101010101010101010101";

		StringBuilder builder = new StringBuilder(hex);
		builder.replace(32, 36, computeChecksum(hex, srcIP, dstIP));
		
		//return DatatypeConverter.parseHexBinary(builder.toString());
		return builder.toString();
	}
	
	/**
	 * Constructs a new TCP Packet with the provided arguments and returns its
	 * packet hex
	 */
	public static String newTCPPacket(String srcIP, String dstIP, int srcPort, int dstPort, int previousAckNumber, 
			int previousSequenceNumber, String append)
	{
		String packetHex = "";

		packetHex += StringUtils.leftPad(Integer.toHexString(srcPort).toUpperCase(), 4, "0");
		packetHex += StringUtils.leftPad(Integer.toHexString(dstPort).toUpperCase(), 4, "0");
				
		packetHex += StringUtils.leftPad(Integer.toHexString(previousAckNumber), 8, "0");
		packetHex += StringUtils.leftPad(Integer.toHexString(previousSequenceNumber), 8, "0");

		packetHex += append;
		//return DatatypeConverter.parseHexBinary(new StringBuilder(packetHex).replace(32, 36, TCPPacket.computeChecksum(packetHex, srcIP, dstIP)).toString());
		return new StringBuilder(packetHex).replace(32, 36, TCPPacket.computeChecksum(packetHex, srcIP, dstIP)).toString();

	}

	private int seqNumber, ackNumber;

	public byte[] getHeaderBytes()
	{
		return packetByteBuffer.array();
	}
	
	public byte[] getPayloadBytes()
	{
		//System.out.println("cap: " + packetByteBuffer.capacity());
		byte []array = new byte[packetByteBuffer.capacity() - headerLength];
		packetByteBuffer.position(headerLength);
		packetByteBuffer.get(array, 0, packetByteBuffer.capacity() - headerLength);
		
		return array;
		//return packetByteBuffer.get(packetByteBuffer.array(), headerLength, packetByteBuffer.array().length).array();
	}
	
	public int getSrcPort()
	{
		return srcPort;
	}

	public int getDstPort()
	{
		return dstPort;
	}

	private int srcPort, dstPort;
	
	public int getSeqNumber()
	{
		return seqNumber;
	}
	
	public int getAckNumber()
	{
		return ackNumber;
	}
	
	private int headerLength;
	
	/** Parse a TCP Packet and populate its fields */
	public void parse()
	{
		byte [] buffer = new byte [4];

		// Get source port
		packetByteBuffer.position(0);
		srcPort = packetByteBuffer.getShort();
		
		// Get destination port
		packetByteBuffer.position(2);
		dstPort = packetByteBuffer.getShort();

		// Get sequence number
		packetByteBuffer.position(4);
		seqNumber = (packetByteBuffer.getInt());
		//System.out.println("Seq: " + seqNumber);

		// Get acknowledgement number
		packetByteBuffer.position(8);
		ackNumber = (packetByteBuffer.getInt());
		//System.out.println("Ack: " + ackNumber);
		
		// Get Header length
		packetByteBuffer.position(12);
		headerLength = (packetByteBuffer.get() & 0x000000FF)>>4;
		headerLength *= 4;
		//System.out.println("header length: " + headerLength);
	}
}