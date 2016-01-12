package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.AttachSimulator;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;

public class UserCommandHandler implements Runnable
{
	private Socket socket;
	private eNodeB enodeb;
	private XMLParser xmlparser;
	
	private AttachSimulator attachSimulator;
	
	private SctpClient sctpClient;
	
	private Object syncObject;
	private int count;

	public UserCommandHandler(Socket socket, eNodeB enodeb, XMLParser xmlparser, SctpClient sctpClient, Object syncObject, int count)
	{
		super();
		this.socket = socket;
		this.enodeb = enodeb;
		this.xmlparser = xmlparser;
		this.sctpClient = sctpClient;
		this.syncObject = syncObject;
		this.count = count;
	}

	private ObjectInputStream OIS = null;
	private ObjectOutputStream OOS = null;
	
	@Override
	public void run()
	{		
		try
		{
			OIS = new ObjectInputStream(socket.getInputStream());
			OOS = new ObjectOutputStream(socket.getOutputStream());
			
			String command = (String) OIS.readObject();
			executeUECommand(command, xmlparser, enodeb);
		}
		
		catch(Exception e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}	
	}
	
	public void executeUECommand(String command, XMLParser xmlparser, eNodeB enodeb)
	{
		if(command.split(";")[0].equals("Attach"))
		{
			//System.out.println("Received IMSI: " + command.split(";")[1]);
			String ueparams = command.split(";")[1] + ";" + command.split(";")[2];
			executeAttachSequence(xmlparser, enodeb, ueparams);
		}
		
		/*Cater for other commands here */
	}

	public void executeAttachSequence(XMLParser xmlparser, eNodeB enodeb, String ueparams)
	{
		// Assign eNBUES1SP id here/..	
		int id;
		//synchronized(syncObject)
		{
			//id = enodeb.getSizeOfUsers() + 1;
			id = count;
		//}
			String eNBUES1APID = Integer.toString(id);// = Integer.toHexString(id);
			
			if(eNBUES1APID.length() == 3)
				eNBUES1APID = "0" + eNBUES1APID;
			if(eNBUES1APID.length() == 2)
				eNBUES1APID = "00" + eNBUES1APID;
			if(eNBUES1APID.length() == 1)
				eNBUES1APID = "000" + eNBUES1APID;
	
			attachSimulator = new AttachSimulator(xmlparser, sctpClient, syncObject);
			
			try
			{
				/** Test Attach Sequence initiation **/
				if(attachSimulator.initiateAttachSequence(xmlparser, ueparams, eNBUES1APID))
				{
					User user = new User();
					user.setTEID(attachSimulator.getTEID());
					user.setIP(attachSimulator.getPDNIpv4().toString().substring(1, attachSimulator.getPDNIpv4().toString().length()));
					user.seteNBUES1APID(eNBUES1APID);
					
					enodeb.setTransportLayerAddressInUserControlInterface(attachSimulator.getTransportLayerAddress());
					
					enodeb.addNewUser(user);
					
					OOS.writeObject(user.getIP());
				}
				
				else
				{
					OOS.writeObject(new String("attachfailure"));
				}
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}
}
