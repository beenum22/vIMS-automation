package com.xflowresearch.nfv.testertool.utils;

import java.net.InetAddress;
import java.nio.ByteBuffer;

import javax.xml.bind.DatatypeConverter;

import org.apache.commons.lang.StringUtils;

public class Ipv4Packet
{
	private ByteBuffer packetByteBuffer;
	
	private String source, destination;
	private int headerLength, packetLength, protocolId;
	private byte [] payload;

	public String getSource()
	{
		return source;
	}

	public String getDestination()
	{
		return destination;
	}

	public int getHeaderLength()
	{
		return headerLength;
	}

	public byte [] getPayloadBytes()
	{
		return payload;
	}

	// private String IpVersion;

	public Ipv4Packet(byte [] bytes)
	{
		//System.out.println(bytes.length + " " + DatatypeConverter.printHexBinary(bytes));

		packetByteBuffer = ByteBuffer.wrap(bytes);
	}

	public static String computeChecksum(String hex)
	{
		byte [] packetBytes = DatatypeConverter.parseHexBinary(hex);
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

		String cs = StringUtils.leftPad(Integer.toHexString(sum), 4, "0");
		
		return cs; 
	}
	
	public static String newIPv4Packet(String type, String srcIP, String dstIP, String transportLayerPacket)
	{
		String headerHex = "450000000000400040060000";
		
		if(type.equals("tcp"))
		{		
			try
			{
				headerHex += StringUtils.leftPad(DatatypeConverter.printHexBinary(InetAddress.getByName(srcIP).getAddress()), 8, "0");
				headerHex += StringUtils.leftPad(DatatypeConverter.printHexBinary(InetAddress.getByName(dstIP).getAddress()), 8, "0");
				//headerHex += transportLayerPacket;
				
				StringBuilder builder = new StringBuilder(headerHex);
				builder.replace(4, 8, StringUtils.leftPad(Integer.toHexString((headerHex.length() + transportLayerPacket.length())/2), 4, "0"));
				builder.replace(20, 24, computeChecksum(builder.toString()));

				return builder.toString() + transportLayerPacket;
			}

			catch(Exception exc)
			{
				exc.printStackTrace();
				return null;
			}
		}
		
		else if(type.equals("udp"))
		{
			headerHex += "116388";
			
			try
			{
				headerHex += DatatypeConverter.printHexBinary(InetAddress.getByName(srcIP).getAddress());
				headerHex += DatatypeConverter.printHexBinary(InetAddress.getByName(dstIP).getAddress());
				
				//System.out.println(packetHex);
				return headerHex;
			}

			catch(Exception exc)
			{
				exc.printStackTrace();
				return null;
			}
		}
		
		return null;
	}

	public void parse()
	{
		try
		{
			byte [] buffer = new byte[4];

			// System.out.println(bytes.length + " " +
			// DatatypeConverter.printHexBinary(bytes));

			// Parse IPVersion and Header Length
			byte byte1;// = new byte [1];
			packetByteBuffer.position(0);
			byte1 = packetByteBuffer.get();

			byte1 = (byte) (byte1 << 4);
			byte1 = (byte) (byte1 >> 4);
			headerLength = byte1;
			//System.out.println("Header length: " + headerLength);

			// Parse Packet Length
			packetByteBuffer.position(2);
			packetLength = packetByteBuffer.getShort();
			//System.out.println("Packet length: " + packetLength);

			// Parse Protocol ID
			packetByteBuffer.position(9);
			protocolId = packetByteBuffer.get();
			//System.out.println("Protocol: " + protocolId);

			// Parse Source IP
			packetByteBuffer.position(12);
			packetByteBuffer.get(buffer, 0, 4);
			//System.out.println("Source: " + InetAddress.getByAddress(buffer).getHostAddress());
			source = InetAddress.getByAddress(buffer).getHostAddress();

			// Parse Destination IP
			packetByteBuffer.position(16);
			packetByteBuffer.get(buffer, 0, 4);
			//System.out.println("Destination: " + InetAddress.getByAddress(buffer).getHostAddress());
			destination = InetAddress.getByAddress(buffer).getHostAddress();

			// Parse IP Payload
			payload = new byte [packetLength - headerLength * 4];
			// System.out.println(payloadBytes.length);
			packetByteBuffer.position(headerLength * 4);
			packetByteBuffer.get(payload, 0, packetLength - headerLength * 4);
			//System.out.println("Payload bytes: " + DatatypeConverter.printHexBinary(payload));
		}

		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
}