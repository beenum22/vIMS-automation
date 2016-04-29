package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.util.ArrayList;

import com.xflowresearch.nfv.testertool.enodeb.Value;

public class MMEController
{
	private SctpClient sctpClient;
	
	private UserControlInterface userControlInterface;
	
	class ReceiverThread implements Runnable
	{
		@Override
		public void run()
		{
			try
			{
				//System.out.println("waiting...");
				while(true)
				{
					String reply = sctpClient.recieveSCTPMessage();
					//System.out.println("got reply");
					
					new Thread(new PacketProcessor(reply)).start();
				}
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}
	
	class PacketProcessor implements Runnable
	{
		String reply;
		
		public PacketProcessor(String reply)
		{
			this.reply = reply;
		}
		
		@Override
		public void run()
		{
			try
			{
				S1APPacket receivedPacket = new S1APPacket();
				receivedPacket.parsePacket(reply);
				
				userControlInterface.onPacketReceived(receivedPacket);
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}
	
	public void setSctpClient(SctpClient sctpClient)
	{
		this.sctpClient = sctpClient;
	}
	
	public MMEController(UserControlInterface userControlInterface)
	{
		this.userControlInterface = userControlInterface;
	}
	
	public void spawnReceiverThread()
	{
		Thread receiverThread = new Thread(new ReceiverThread());
		receiverThread.start();
	}
	
	public S1APPacket initS1Signalling(String type, String procCode, String criticality, ArrayList <Value> values, Boolean recieve)
	{
		S1APPacket pac = new S1APPacket(type, procCode, criticality, values.size());
		
		for(int i = 0; i < values.size(); i++)
		{
			pac.addValue(values.get(i).typeOfValue, values.get(i).criticality, values.get(i).value.length() / 2, values.get(i).value);
		}
		
		pac.createPacket();
		byte [] message = pac.getBytePacket();
		
		//logger.info("Sending Packet -- " + pac.toString());
		
		sctpClient.sendProtocolPayload(message, 18);
		
		if(recieve == true)
		{
			String reply = sctpClient.recieveSCTPMessage();
		
			S1APPacket recievedPacket = new S1APPacket();
			recievedPacket.parsePacket(reply);
		
			//logger.info("Received Packet -- " + recievedPacket.toString());
		
			return recievedPacket;
		}
		
		return null;
	}
}