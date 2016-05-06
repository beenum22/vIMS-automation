package com.xflowresearch.nfv.testertool.enodeb;

import java.net.InetAddress;
import java.util.ArrayList;

import com.xflowresearch.nfv.testertool.common.ConfigHandler;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.MMEController;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.UserControlInterface;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;
import com.xflowresearch.nfv.testertool.enodeb.s1u.UserDataInterface;
import com.xflowresearch.nfv.testertool.ue.UEController;

/**
 * eNodeB
 * 
 * eNodeB class that executes on the eNodeB thread and initiates the eNodeB
 * functionality.
 *
 * 
 * @author ahmadarslan
 */
public class eNodeB// implements Runnable
{
	//private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");
	private ConfigHandler xmlparser;

	private ArrayList <User> users;
	private Object userListLock;

	private SctpClient sctpClient;
	private UserDataInterface userDataInterface;
	private UserControlInterface userControlInterface;
	
	private MMEController mMeController;
	private UEController ueController;
	
	public eNodeB(ConfigHandler xmlParser, UEController ueController)
	{
		users = new ArrayList <User>();
		this.xmlparser = xmlParser;
		sctpClient = new SctpClient(xmlparser);
		userDataInterface = new UserDataInterface();
		userControlInterface = new UserControlInterface(xmlParser, this, sctpClient, ueController);
		mMeController = new MMEController(userControlInterface);
		
		this.ueController = ueController;
		
		userListLock = new Object();
	}

	/** Return this eNodeB's UserControlInterface */
	public UserControlInterface getUserControlInterface()
	{
		if(this.userControlInterface != null)
			return userControlInterface;
		
		else return null;
	}
	
//	public Logger getLogger()
//	{
//		return eNodeB.logger;
//	}

	/**
	 * Establish S1Signalling with MME..
	 * 
	 * @param configHandler
	 */
	public Boolean establishS1Signalling()
	{
		try
		{
			if(sctpClient.connectToHost(xmlparser.getMMEIP(), Integer.parseInt(xmlparser.getMMEPort())))
			{			
				mMeController.setSctpClient(sctpClient);
	
				ArrayList <Value> values = new ArrayList <Value>();
				values.add(new Value("GlobalENBID", "reject", xmlparser.getS1signallingParams().GlobalENBID));
				values.add(new Value("eNBname", "ignore", xmlparser.getS1signallingParams().eNBname));
				values.add(new Value("SupportedTAs", "reject", xmlparser.getS1signallingParams().SupportedTAs));
				values.add(new Value("DefaultPagingDRX", "ignore", xmlparser.getS1signallingParams().DefaultPagingDRX));
	
				S1APPacket recievedPacket = mMeController.initS1Signalling("InitiatingMessage", "S1Setup", "reject", values, true);
	
				if(recievedPacket.getType().equals("SuccessfulOutcome"))
				{
					mMeController.spawnReceiverThread();
					return true;
				}
				
				else
				{
					System.out.println("Failed to connect with MME");
					//logger.error("Failed to connect with MME");
					return false;
				}
			}
			
			else
			{
				System.out.println("Failed to connect with MME");
				//logger.error("Failed to connect with MME");
				return false;
			}
		}		
	
		catch(Exception exc)
		{
			exc.printStackTrace();
			return false;
		}
	}
	
	//@Override
	public void run()
	{
		//logger.info("eNodeB started");

		/*
		 * establish s1 signalling with the MME
		 */
		if(establishS1Signalling())
		{
			//logger.info("S1 Signaling Successfully Established");

			/* Listen for UE Commands for Control Plane Signaling */
			//userControlInterface.listenForUserControlCommands(xmlparser, this, sctpClient);

			/* Listen for UE Data for User Plane */
			//userDataInterface.listenForUserDataTraffic(this);
		}

		else
		{
			System.out.println("Unable to establish S1Signalling with MME");
			//logger.error("Unable to establish S1Signalling with MME");
		}
	}

	public void setTransportLayerAddress(InetAddress tla)
	{
		this.transportLayerAddress = tla;
	}
	
	public void setTransportLayerAddressInUserControlInterface(InetAddress transportLayerAddress)
	{
		userDataInterface.setTransportLayerAddress(transportLayerAddress);
	}

	private InetAddress transportLayerAddress;
	
	public InetAddress getTransportLayerAddress()
	{
		return this.transportLayerAddress;
	}
	
	public void addNewUser(User user)
	{
		synchronized(userListLock)
		{
			users.add(user);
		}
		
		System.out.println("eNBUES1APID: " + user.geteNBUES1APID() + " New User Added - TEID:" + user.getTEID());
	}

	public User getUser(String enbUES1APID)
	{
		String id = enbUES1APID.toUpperCase();
		
		synchronized (userListLock)
		{
			for(User u:users)
			{
				//System.out.println("searching: " + enbUES1APID + " " + u.geteNBUES1APID());
				
				if(u.geteNBUES1APID().equals(id))
				{
					return u;
				}
			}
		}
		
		System.out.println("not found");
		return null;
	}
	
	public User getUser(int index)
	{
		return users.get(index);
	}
	
	public int getSizeOfUsers()
	{
		return users.size();
	}
}
