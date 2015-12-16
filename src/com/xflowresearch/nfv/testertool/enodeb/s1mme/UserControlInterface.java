package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.net.InetAddress;
import java.net.ServerSocket;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;

public class UserControlInterface
{
	public void listenForUserControlCommands(XMLParser xmlparser, eNodeB enodeb, SctpClient sctpClient)
	{
		new Thread()
		{
			public void run()
			{
				ServerSocket serverSocket = null;
				
				try
				{
					serverSocket = new ServerSocket(9877, 20, InetAddress.getByName(xmlparser.geteNBIP()));
				}
				
				catch(Exception exc)
				{
					System.out.println("UserControlInterface: Bind Exception" + exc.getMessage());
					//exc.printStackTrace();
				}
				
				while(true)
				{
					try
					{
						new Thread(new UserCommandHandler(serverSocket.accept(), enodeb, xmlparser, sctpClient)).start();					
					}
					
					catch(Exception exc)
					{
						exc.printStackTrace();
					}
				}
				
				/* Needs graceful termination
				 * serverSocket.close(); */
			}
		}.start();
	}
}
