package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.AttachSimulator;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;

public class UserCommandHandler implements Runnable
{

	private String command;
	private DatagramSocket serverSocket;
	private eNodeB enodeb;
	private XMLParser xmlparser;
	private AttachSimulator attachSimulator;
	
	private InetAddress IPAddress;
	private int port;
	
	private SctpClient sctpClient;

	public UserCommandHandler(String command, DatagramSocket serverSocket, eNodeB enodeb, XMLParser xmlparser, InetAddress IPAddress, int port, SctpClient sctpClient)
	{
		super();
		this.command = command;
		this.serverSocket = serverSocket;
		this.enodeb = enodeb;
		this.xmlparser = xmlparser;
		this.IPAddress = IPAddress;
		this.port = port;
		this.sctpClient = sctpClient;
	}

	@Override
	public void run()
	{
		User user;
		Object reply = executeUECommand(command, xmlparser, enodeb);

		byte [] sendData = new byte[1024];
		if(reply != null)
		{
			String pdnipv4 = null;
			if(reply.getClass().equals(com.xflowresearch.nfv.testertool.enodeb.s1u.User.class))
			{
				user = (User) reply;
				pdnipv4 = user.getIP();
				enodeb.addNewUser(user);
			}
			sendData = pdnipv4.getBytes();
		}
		else
		{
			sendData = new String("attachfailure").getBytes();
		}
		DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, IPAddress, port);
		try
		{
			serverSocket.send(sendPacket);
		}
		catch(IOException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public Object executeUECommand(String command, XMLParser xmlparser, eNodeB enodeb)
	{
		if(command.split(";")[0].equals("Attach"))
		{
			//System.out.println("Received IMSI: " + command.split(";")[1]);
			String ueparams = command.split(";")[1] + ";" + command.split(";")[2];
			return executeAttachSequence(xmlparser, enodeb, ueparams);
		}

		return null;
	}

	public Object executeAttachSequence(XMLParser xmlparser, eNodeB enodeb, String ueparams)
	{
		// Assign eNBUES1SP id here/..
		int id = enodeb.getSizeOfUsers() + 1;
		String eNBUES1APID = Integer.toHexString(id);
		
		if(eNBUES1APID.length() == 3)
			eNBUES1APID = "0" + eNBUES1APID;
		if(eNBUES1APID.length() == 2)
			eNBUES1APID = "00" + eNBUES1APID;
		if(eNBUES1APID.length() == 1)
			eNBUES1APID = "000" + eNBUES1APID;

		attachSimulator = new AttachSimulator(xmlparser, sctpClient);
		
		/** Test Attach Sequence initiation **/
		if(attachSimulator.initiateAttachSequence(xmlparser, ueparams, eNBUES1APID))
		{
			User user = new User();
			user.setTEID(attachSimulator.getTEID());
			user.setIP(attachSimulator.getPDNIpv4().toString().substring(1, attachSimulator.getPDNIpv4().toString().length()));
			enodeb.setTransportLayerAddressInUserControlInterface(attachSimulator.getTransportLayerAddress());
			return user;
		}

		return null;
	}
}
