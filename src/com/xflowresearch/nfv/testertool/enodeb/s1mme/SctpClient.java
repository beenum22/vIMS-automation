package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;

import com.sun.nio.sctp.MessageInfo;
import com.sun.nio.sctp.SctpChannel;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * SctpClient
 * 
 * SCTP wrapper class to establish SCTP connection to a server and send and
 * receive messages to and from the server
 * 
 * @author ahmadarslan
 */
public class SctpClient
{
	private Boolean isConnected;
	private SocketAddress socketAddress;
	private SctpChannel sctpChannel;

	/** Logger to log the messages and Errors **/
	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");

	public SctpClient()
	{
		isConnected = false;
	}

	public Boolean isConnected()
	{
		return isConnected;
	}

	/**
	 * Connect to the SCTP Server
	 */
	public boolean connectToHost(String ip, int port)
	{
		InetAddress address = null;
		try
		{
			address = InetAddress.getByName(ip);
		}
		catch(UnknownHostException e)
		{
			logger.error("Could not build SCTP Server address {}!", ip);
			e.printStackTrace();
		}
		socketAddress = new InetSocketAddress(address, port);

		try
		{
			sctpChannel = SctpChannel.open();
			// sctpChannel.bind(new InetSocketAddress(36412));
			sctpChannel.bind(new InetSocketAddress(0));// '0' instead of user
													   // defined port to get an
													   // available port
													   // assigned by the OS!!
			sctpChannel.connect(socketAddress, 1, 1);
		}
		catch(IOException e)
		{
			logger.error("SCTP connection to server was refused!");
			return false;
		}
		logger.info("SCTP Connection Established ip:{} port:{}", ip, port);
		isConnected = true;
		return true;
	}

	/**
	 * Disconnect from the SCTP Server
	 */
	public void disconnectFromHost()
	{
		try
		{
			sctpChannel.shutdown();
			isConnected = false;
		}
		catch(IOException e)
		{
			logger.error("Unable to close SCTP channel with Server!");
			e.printStackTrace();
		}
	}

	/**
	 * Send protocol payload specified by the protocol id over open SCTP Channel
	 */
	public void sendProtocolPayload(byte [] payload, int protocolID)
	{
		if(isConnected)
		{
			final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);
			MessageInfo messageInfo = MessageInfo.createOutgoing(null, 0);

			byteBuffer.put(payload);
			byteBuffer.flip();

			messageInfo.payloadProtocolID(protocolID);

			try
			{
				sctpChannel.send(byteBuffer, messageInfo);
			}
			catch(Exception e)
			{
				logger.error("SCTP channel closed - could not send data");
				// e.printStackTrace();
			}
		}
		else logger.error("SCTP connection not active!");
	}

	/**
	 * Send data over open SCTP Channel
	 */
	public void sendData(byte [] payload)
	{
		if(isConnected)
		{
			final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);
			final MessageInfo messageInfo = MessageInfo.createOutgoing(null, 0);

			byteBuffer.put(payload);
			byteBuffer.flip();

			try
			{
				sctpChannel.send(byteBuffer, messageInfo);
			}
			catch(Exception e)
			{
				logger.error("SCTP channel closed - could not send data");
				e.printStackTrace();
			}
		}
		else logger.error("SCTP connection not active");
	}

	/**
	 * Listen for SCTP data from Server
	 */
	public synchronized void recievingThread()
	{

		while(isConnected)
		{
			final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);
			MessageInfo messageInfo = null;

			try
			{
				messageInfo = sctpChannel.receive(byteBuffer, null, null);
			}
			catch(IOException e)
			{
				logger.error("SCTP Message read error!");
				e.printStackTrace();
			}

			byteBuffer.flip();

			byte [] data = new byte[byteBuffer.remaining()];
			byteBuffer.get(data);

			String hexPayload = bytesToHex(data);

			handleMessageFromHost(messageInfo, hexPayload);
		}
	}

	/**
	 * Handle the message from the SCTP Server
	 */
	public void handleMessageFromHost(MessageInfo messageInfo, String hexPayload)
	{

		if(hexPayload.length() != 0)
		{
			logger.info("SCTP Message recieved");

			S1APPacket recievedPacket = new S1APPacket();
			recievedPacket.parsePacket(hexPayload);
		}
	}

	/**
	 * Convert byte array to hex String
	 */
	final protected static char [] hexArray = "0123456789ABCDEF".toCharArray();

	public static String bytesToHex(byte [] bytes)
	{
		char [] hexChars = new char[bytes.length * 2];
		for(int j = 0; j < bytes.length; j++)
		{
			int v = bytes[j] & 0xFF;
			hexChars[j * 2] = hexArray[v >>> 4];
			hexChars[j * 2 + 1] = hexArray[v & 0x0F];
		}
		return new String(hexChars);
	}

	//////////////////// new method to recieve synchronous messages/////////////
	public String recieveSCTPMessage()
	{
		final ByteBuffer byteBuffer = ByteBuffer.allocate(64000);
		MessageInfo messageInfo = null;

		try
		{
			messageInfo = sctpChannel.receive(byteBuffer, null, null);
		}
		catch(IOException e)
		{
			logger.error("SCTP Message read error!");
			e.printStackTrace();
		}

		byteBuffer.flip();

		byte [] data = new byte[byteBuffer.remaining()];
		byteBuffer.get(data);

		String hexPayload = bytesToHex(data);
		return hexPayload;
		// handleMessageFromHost(messageInfo, hexPayload);

	}

}
