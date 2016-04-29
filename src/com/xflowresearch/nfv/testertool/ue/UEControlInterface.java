package com.xflowresearch.nfv.testertool.ue;

import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;

public class UEControlInterface
{
	Socket clientSocket = null;
	
	ObjectOutputStream OOS = null;
	ObjectInputStream OIS = null;
	
	public String sendAttachRequest(String command, String eNBIP, String eNBPort)
	{
		String pdnipv4 = null;
			
		try
		{
			clientSocket = new Socket(eNBIP, Integer.parseInt(eNBPort));
		}
		
		catch(Exception exc)
		{
			System.out.println("UEControlInterface: Error in connecting: " + exc.getMessage());
		}
		
		try
		{
			OOS = new ObjectOutputStream(clientSocket.getOutputStream());
			OIS = new ObjectInputStream(clientSocket.getInputStream());
		}
		
		catch(Exception exc)
		{
			System.out.println("UEControlInterface: Error in opening streams: " + exc.getMessage());
		}
		
		try
		{
			OOS.writeObject(command);
		}
		
		catch(Exception exc)
		{
			System.out.println("UEControlInterface: Error in sending: " + exc.getMessage());			
		}
		
		try
		{
			pdnipv4 = (String) OIS.readObject();
		}
		
		catch(Exception e)
		{
			System.out.println("UEControlInterface: Error in receiving: " + e.getMessage());			
		}
		
		return pdnipv4;
	}
	
	public String sendControlCommand(String command)
	{		
		try
		{
			OOS.writeObject(command);
		}
		
		catch(Exception exc)
		{
			System.out.println("UEControlInterface: Error in sending: " + exc.getMessage());			
		}
		
		try
		{
			//Get reply here
		}
		
		catch(Exception e)
		{
			System.out.println("UEControlInterface: Error in receiving: " + e.getMessage());			
		}

		return null;
	}
}
