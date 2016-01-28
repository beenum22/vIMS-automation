package com.xflowresearch.nfv.testertool.ue;

import java.io.EOFException;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;
import java.util.TreeMap;
import com.xflowresearch.nfv.testertool.common.XMLParser;

public class UEController
{
	boolean debugOnScreen = true;
	
	private TreeMap<String, UE> UEs;
	
	private Object uEListLock;
	private Object socketLock;
	Object counterLock;
	
	private XMLParser xmlparser;
	
	public UEController(XMLParser xmlparser)
	{
		UEs = new TreeMap<>();
		
		uEListLock = new Object();
		socketLock = new Object();
		counterLock = new Object();
		
		this.xmlparser = xmlparser;
	}
	
	public void addUE(UE ue)
	{
		synchronized(uEListLock)
		{
			UEs.put(ue.geteNBUES1APID(), ue);
		}
	}
		
	public void sendAttachRequest(UE ue)
	{		
		addUE(ue);
		
		try
		{
			synchronized(socketLock)
			{
				OOS.writeObject("Attach;" + ue.geteNBUES1APID() + ";" + ue.UEParameters.toString());
			}
			
			//System.out.println("Sent: " + "Attach;" + ue.geteNBUES1APID() + ";" + ue.UEParameters.toString());
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	Socket connectionSocket = null;
	ObjectOutputStream OOS = null;
	ObjectInputStream OIS = null;
	
	public void initENBConnection()
	{
		try
		{
			connectionSocket = new Socket(xmlparser.geteNBIP(), Integer.parseInt(xmlparser.geteNBPort()));
		}
		
		catch(Exception exc)
		{
			if(debugOnScreen)
			{
				System.out.println("UEController failed to connect to eNB: " + exc.getMessage());
			}
			
			exc.printStackTrace();
		}
		
		try
		{
			OOS = new ObjectOutputStream(connectionSocket.getOutputStream());
			OIS = new ObjectInputStream(connectionSocket.getInputStream());
		}
		
		catch(Exception exc)
		{
			if(debugOnScreen)
			{
				System.out.println("UEController failed to open streams: " + exc.getMessage());
			}
			
			exc.printStackTrace();
		}
	}
	
	//private volatile boolean isConnected = false;
	
	int successfulAttaches = 0;
	int failedAttaches = 0;
	
	class ResponseProcessor implements Runnable
	{
		String response;
		
		public ResponseProcessor(String response)
		{
			this.response = response;
		}
		
		@Override
		public void run()
		{
			UE temp;
			
			if(!response.split(";")[1].equals("attachfailure"))
			{
				
				synchronized(uEListLock)
				{
					temp = UEs.get((response.split(";")[0]));
				}
				
				synchronized(counterLock)
				{
					successfulAttaches++;
				}
				
				if(temp != null)
				{
					System.out.println("Successfully attached - eNBUES1APID = " + response.split(";")[0]);
					temp.processAttachResponse(response.split(";")[1]);
				}
				
				else
				{
					//System.out.println("UE not found");
				}
			}
			
			else
			{
				System.out.println(response.split(";")[0] + " failed");
				synchronized(counterLock)
				{
					failedAttaches++;
				}
			}
		}
	}
	
	public void spawnReceiverThread()
	{		
		new Thread(new Runnable()
		{
			@Override
			public void run()
			{
				//System.out.println("Now listening...");
				
				while(true)
				{	
					try
					{
						String response = (String) OIS.readObject();
						new Thread(new ResponseProcessor(response)).start();
					}
					
					catch(EOFException eofExc)
					{
						try
						{
							connectionSocket.close();
							System.out.println("Connection to eNB closed");
							
							System.out.println("Successful attaches: " + successfulAttaches);
							System.out.println("Failed attaches: " + failedAttaches);
							
							break;
						}
						
						catch(IOException ioExc)
						{
							
						}
					}
					
					catch(Exception exc)
					{
						exc.printStackTrace();
					}
				}
			}
		}).start();
	}
}