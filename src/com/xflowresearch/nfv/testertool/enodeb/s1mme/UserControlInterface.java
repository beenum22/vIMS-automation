package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.EOFException;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.TreeMap;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;

public class UserControlInterface
{
	TreeMap<String, UserCommandHandler>list;
	//ArrayList<UserCommandHandler> list;
	
	private Object eNodeBLock;
	private Object outputStreamLock;
	
	private ObjectInputStream OIS;
	private ObjectOutputStream OOS;
	
	public UserControlInterface()
	{
		list = new TreeMap<>();
		//list = new ArrayList<>();
		
		listLock = new Object();
		eNodeBLock = new Object();
		outputStreamLock = new Object();
	}
	
	boolean exit = false;
	
	public Object listLock;
	
	private Socket socket;
	
	public void onPacketReceived(S1APPacket receivedPacket)
	{		
		//System.out.println(receivedPacket.geteNBUES1APID());
		
		try
		{
			String eNBUES1APID;

			if((eNBUES1APID = receivedPacket.geteNBUES1APID()) != null)
			{				
				UserCommandHandler temp = null;
				
				synchronized(listLock)
				{
					temp = list.get(receivedPacket.geteNBUES1APID().toLowerCase());
				}
				
				if(temp != null)
				{
					temp.onPacketReceived(receivedPacket);
				}
				
				else
				{
					//System.out.println("not found");
				}
			}
			
			else
			{
				System.out.println("no destination: " + receivedPacket.getProcCode());
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	public void listenForUserControlCommands(XMLParser xmlparser, eNodeB enodeb, SctpClient sctpClient)
	{
		new Thread()
		{
			public void run()
			{
				ServerSocket serverSocket = null;
				
				try
				{
					serverSocket = new ServerSocket(Integer.parseInt(xmlparser.geteNBPort()), 100000000, InetAddress.getByName(xmlparser.geteNBIP()));
					socket = serverSocket.accept();
					
					OIS = new ObjectInputStream(socket.getInputStream());
					OOS = new ObjectOutputStream(socket.getOutputStream());
				}
				
				catch(Exception exc)
				{
					System.out.println("UserControlInterface: Bind Exception" + exc.getMessage());
					exc.printStackTrace();
				}
				
				//System.out.println("Listening for commands...");
				
				while(!exit)
				{
					try
					{
						String command = (String) OIS.readObject();
						//System.out.println(command.split(";")[1]);
						
						new Thread(new Runnable()
						{							
							@Override
							public void run()
							{
								String eNBUES1APID = command.split(";")[1];
								
								//System.out.println(eNBUES1APID);
								
								UserCommandHandler temp = new UserCommandHandler(eNBUES1APID, command, enodeb, xmlparser, sctpClient, eNodeBLock, OOS, outputStreamLock);
								
								synchronized(listLock)
								{
									//list.add(temp);
									list.put(eNBUES1APID, temp);
									//System.out.println(eNBUES1APID);
								}
								
								new Thread(temp).start();
							}
						}).start();
					}
					
					catch(EOFException exc)
					{
						try
						{
							System.out.println("TCP Connection with UEController closed");
							serverSocket.close();
							exit = true;
						}
						
						catch(IOException ioexc)
						{
							ioexc.printStackTrace();
						}
					}
					
					catch(Exception exc)
					{
						exc.printStackTrace();
					}
				}
			}
		}.start();
	}
}
