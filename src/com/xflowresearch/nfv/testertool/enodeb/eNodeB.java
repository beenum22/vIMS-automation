package com.xflowresearch.nfv.testertool.enodeb;

import java.net.InetAddress;
import java.util.ArrayList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
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

	@Override
	public void run()
	{
		logger.info("eNodeB started");

		AttachSimulator as = new AttachSimulator(xmlparser);

		/*
		 * establish s1 signalling with the MME
		 */
		if(as.establishS1Signalling(xmlparser, sctpClient))
		{
			logger.info("S1 Signaling Successfully Established");

			/** Listen for UE Commands for Control Plane Signaling **/
			userControlInterface.listenForUserControlCommands(xmlparser, as, this);

			/** Listen for UE Data for User Plane **/
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
		System.out.println("New User Added - TEID:" + user.getTEID());
	}

	public synchronized User getUser(int index)
	{
		return users.get(index);
	}
	public synchronized int getSizeOfUsers(){
		return users.size();
	}
}
