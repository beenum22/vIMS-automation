package com.xflowresearch.nfv.testertool.ue;

import java.io.ByteArrayInputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.Inet4Address;
import java.net.InetAddress;

import javax.xml.bind.DatatypeConverter;

import org.apache.commons.lang.StringUtils;

import org.pcap4j.packet.IpV4Packet;
import org.pcap4j.packet.IpV4Packet.IpV4Header;
import org.pcap4j.packet.IpV4Rfc1349Tos;
import org.pcap4j.packet.TcpPacket;
import org.pcap4j.packet.TcpPacket.TcpHeader;
import org.pcap4j.packet.namednumber.IpNumber;
import org.pcap4j.packet.namednumber.IpVersion;
import org.pcap4j.packet.namednumber.TcpPort;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1u.GTPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;
import com.xflowresearch.nfv.testertool.utils.Ipv4Packet;
import com.xflowresearch.nfv.testertool.utils.TCPPacket;

/**
 * UE Class that is used to simulate User Equipment. Attaches to 
 * the eNodeB and simulated HTTP send/receive
 *
 * @author Aamir Khan
 */

public class UE implements Runnable
{
	//private static final Logger logger = LoggerFactory.getLogger("UELogger");

	UEParameters UEParameters;
	private XMLParser xmlparser;
	private String pdnipv4;
	private User user;
	private UEController uEController;
	private String eNBUES1APID;
		
	/*State variables */
	boolean syn, httpResponse, finAck, okAck;
	
	public UE(int id, UEParameters UEParams, XMLParser xmlparser, UEController uEController)
	{
		UEParameters = UEParams;	
		this.eNBUES1APID = StringUtils.leftPad(Integer.toHexString(id), 4, "0");
		this.uEController = uEController;
		this.xmlparser = xmlparser;
		
		syn = httpResponse = finAck = okAck = false;
	}
	
	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}
	
	public String getPdnipv4()
	{
		return pdnipv4;
	}
	
	public void processPacket(IpV4Packet p)
	{
		IpV4Header ipv4Header = null;
		TcpPacket tcpPacket = null;
		TcpHeader tcpHeader = null;
		
		try
		{
			ipv4Header = p.getHeader();
			tcpPacket = (TcpPacket) p.getPayload();
			tcpHeader = tcpPacket.getHeader();
			
			//System.out.println("Received: " + DatatypeConverter.printHexBinary(p.getRawData()));
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
			
		if(syn && !httpResponse) // Syn has been sent - now send Ack and HttpRequest
		{
			try
			{
				TcpPacket.Builder tcpBuilder = new TcpPacket.Builder();
				IpV4Packet.Builder ipv4Builder = new IpV4Packet.Builder();
			
				tcpBuilder.srcPort(TcpPort.getInstance((short)44000)).
					   dstPort(TcpPort.getInstance((short)80)).
					   srcAddr(InetAddress.getByName(user.getIP())).
					   dstAddr(InetAddress.getByName(xmlparser.getWebServerIP())).
					   dataOffset((byte)10).
					   ack(true).
					   sequenceNumber(tcpHeader.getAcknowledgmentNumber()).
					   acknowledgmentNumber(tcpHeader.getSequenceNumber()+1).
					   correctLengthAtBuild(true).
					   correctChecksumAtBuild(true).
					   window((short)1460);
				
				ipv4Builder.version(IpVersion.IPV4).
						ihl((byte)5).
						tos(IpV4Rfc1349Tos.newInstance((byte)0)).
						identification((short)0).
						srcAddr((Inet4Address)InetAddress.getByName(user.getIP())).
						dstAddr((Inet4Address)InetAddress.getByName(xmlparser.getWebServerIP())).
						protocol(IpNumber.TCP).
						ttl((byte)64).
						dontFragmentFlag(true).
						correctChecksumAtBuild(true).
						correctLengthAtBuild(true).
						payloadBuilder(tcpBuilder);
				
				sendGTPPacket(DatatypeConverter.printHexBinary(ipv4Builder.build().getRawData()));
				
				Thread.sleep(500);
				
				String getHex = Ipv4Packet.newIPv4Packet("tcp", user.getIP(), xmlparser.getWebServerIP(), 
						TCPPacket.newTCPPacket(user.getIP(), xmlparser.getWebServerIP(), 44000, 80,
						tcpHeader.getAcknowledgmentNumber(), tcpHeader.getSequenceNumber()+1, 
						"5018007300000000" +
						"474554202f526573706f6e7365536572766c657420485454502f312e310d0a486f7374" + 
						"3a203137322e31372e322e320d0a436f6e6e656374696f6e3a20636c6f73650d0a0d0a"));
				
				sendGTPPacket(getHex);
			
				httpResponse = true;
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
		
		else if(syn && httpResponse && !okAck)
		{
			if(tcpHeader.getPsh() == false)
			{
				//This handles the Ack for the get request from the server - Do nothing in this case
			}

			else
			{				
				try
				{
					System.out.println(new String(tcpPacket.getPayload().getRawData()));					

					TcpPacket.Builder tcpBuilder = new TcpPacket.Builder();
					IpV4Packet.Builder ipv4Builder = new IpV4Packet.Builder();

					tcpBuilder.srcPort(TcpPort.getInstance((short)44000)).
					   dstPort(TcpPort.getInstance((short)80)).
					   srcAddr(InetAddress.getByName(user.getIP())).
					   dstAddr(InetAddress.getByName(xmlparser.getWebServerIP())).
					   dataOffset((byte)10).
					   ack(true).
					   fin(true).
					   sequenceNumber(tcpHeader.getAcknowledgmentNumber()).
					   acknowledgmentNumber(tcpHeader.getSequenceNumber() + tcpPacket.getPayload().length()+1).
					   correctLengthAtBuild(true).
					   correctChecksumAtBuild(true).
					   window((short)1460);
				
					ipv4Builder.version(IpVersion.IPV4).
						ihl((byte)5).
						tos(IpV4Rfc1349Tos.newInstance((byte)0)).
						identification((short)0).
						srcAddr((Inet4Address)InetAddress.getByName(user.getIP())).
						dstAddr((Inet4Address)InetAddress.getByName(xmlparser.getWebServerIP())).
						protocol(IpNumber.TCP).
						ttl((byte)64).
						dontFragmentFlag(true).
						correctChecksumAtBuild(true).
						correctLengthAtBuild(true).
						payloadBuilder(tcpBuilder);
					
					sendGTPPacket(DatatypeConverter.printHexBinary(ipv4Builder.build().getRawData()));
				}
				
				catch(Exception exc)
				{
					exc.printStackTrace();
				}
				
				okAck = true;
			}
		}
	}
		
	public void simulateHttpRequest(User user)
	{
		this.pdnipv4 = user.getIP();
		this.user = user;
		
		sendSyn();
	}
	
	private DatagramSocket socket;

	public void sendSyn()
	{		
		try
		{
			socket = new DatagramSocket();
			
			TcpPacket.Builder tcpBuilder = new TcpPacket.Builder();
			IpV4Packet.Builder ipv4Builder = new IpV4Packet.Builder();
		
			tcpBuilder.srcPort(TcpPort.getInstance((short)44000)).
				   dstPort(TcpPort.getInstance((short)80)).
				   srcAddr(InetAddress.getByName(user.getIP())).
				   dstAddr(InetAddress.getByName(xmlparser.getWebServerIP())).
				   dataOffset((byte)10).
				   syn(true).
				   sequenceNumber(0).
				   acknowledgmentNumber(0).
				   correctLengthAtBuild(true).
				   correctChecksumAtBuild(true).
				   window((short)1460);
			
			ipv4Builder.version(IpVersion.IPV4).
					ihl((byte)5).
					tos(IpV4Rfc1349Tos.newInstance((byte)0)).
					identification((short)0).
					srcAddr((Inet4Address)InetAddress.getByName(user.getIP())).
					dstAddr((Inet4Address)InetAddress.getByName(xmlparser.getWebServerIP())).
					protocol(IpNumber.TCP).
					ttl((byte)64).
					dontFragmentFlag(true).
					correctChecksumAtBuild(true).
					correctLengthAtBuild(true).
					payloadBuilder(tcpBuilder);
			
			String packetHex = DatatypeConverter.printHexBinary(ipv4Builder.build().getRawData());
			sendGTPPacket(packetHex);
			
			syn = true;
		}
		
		catch(Exception e)
		{
			e.printStackTrace();
		}	   
	}
	
	public void sendGTPPacket(String packetHex)
	{
		try
		{
			GTPacket gtpacket = new GTPacket("001", 1, 0, 0, 0, 0);
			gtpacket.setMessageType("ff");
			gtpacket.setLength(packetHex.length() / 2);
			gtpacket.setTEID(user.getTEID());
			gtpacket.setTPDU(packetHex);
			
			DatagramPacket packet = new DatagramPacket(gtpacket.getPacket(), gtpacket.getPacket().length, 
					user.getTransportLayerAddress(), 2152);
			
			socket.send(packet);
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	@Override
	public void run()
	{
		uEController.sendAttachRequest(this);
	}
}