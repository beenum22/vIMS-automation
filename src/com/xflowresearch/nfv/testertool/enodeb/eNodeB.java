package com.xflowresearch.nfv.testertool.enodeb;

import java.net.InetAddress;
import java.util.ArrayList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.UserControlInterface;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;
import com.xflowresearch.nfv.testertool.enodeb.s1u.UserDataInterface;

/**
 * eNodeB
 * 
 * eNodeB class that executes on the eNodeB thread and initiates the eNodeB
 * functionality.
 *
 * 
 * @author ahmadarslan
 */
public class eNodeB implements Runnable
{
	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");
	private XMLParser xmlparser;

	private ArrayList <User> users;

	private SctpClient sctpClient;
	private UserDataInterface userDataInterface;
	private UserControlInterface userControlInterface;
	
	private AttachSimulator S1AS;

	public eNodeB()
	{
		users = new ArrayList <User>();

		sctpClient = new SctpClient();
		userDataInterface = new UserDataInterface();
		userControlInterface = new UserControlInterface();
	}

	public void setXMLParser(XMLParser xmlparser)
	{
		this.xmlparser = xmlparser;
	}

	public Logger getLogger()
	{
		return eNodeB.logger;
	}

	/**
	 * Establish S1Signalling with MME..
	 * 
	 * @param xmlparser
	 */
	public Boolean establishS1Signalling()
	{
		if(sctpClient.connectToHost(xmlparser.getMMEIP(), Integer.parseInt(xmlparser.getMMEPort())))
		{			
			S1AS = new AttachSimulator(xmlparser, sctpClient);
			
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("GlobalENBID", "reject", xmlparser.getS1signallingParams().GlobalENBID));
			values.add(new Value("eNBname", "ignore", xmlparser.getS1signallingParams().eNBname));
			values.add(new Value("SupportedTAs", "reject", xmlparser.getS1signallingParams().SupportedTAs));
			values.add(new Value("DefaultPagingDRX", "ignore", xmlparser.getS1signallingParams().DefaultPagingDRX));
	
			S1APPacket recievedPacket = S1AS.sendS1APacket("InitiatingMessage", "S1Setup", "reject", values, true);
	
			if(recievedPacket.getType().equals("SuccessfulOutcome"))
			{
				return true;
			}
			
			else
			{
				logger.error("Failed to connect with MME");
				return false;
			}
		}
		
		else
		{
			logger.error("Failed to connect with MME");
			return false;
		}
	}
	
	@Override
	public void run()
	{
		logger.info("eNodeB started");

		/*
		 * establish s1 signalling with the MME
		 */
		if(establishS1Signalling())
		{
			logger.info("S1 Signaling Successfully Established");

			/* Listen for UE Commands for Control Plane Signaling */
			userControlInterface.listenForUserControlCommands(xmlparser, this, sctpClient);

			/* Listen for UE Data for User Plane */
			userDataInterface.listenForUserDataTraffic(this);
		}
		
		else
		{
			logger.error("Unable to establish S1Signalling with MME");
		}
	}

	public synchronized void setTransportLayerAddressInUserControlInterface(InetAddress transportLayerAddress)
	{
		userDataInterface.setTransportLayerAddress(transportLayerAddress);
	}

	public synchronized void addNewUser(User user)
	{
		users.add(user);
		System.out.println("eNBUES1APID: " + user.geteNBUES1APID() + " New User Added - TEID:" + user.getTEID());
	}

	public synchronized User getUser(int index)
	{
		return users.get(index);
	}
	
	public int getSizeOfUsers()
	{
		synchronized (S1AS)
		{
			return users.size();
		}
	}
}
