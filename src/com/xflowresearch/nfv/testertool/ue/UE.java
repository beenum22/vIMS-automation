package com.xflowresearch.nfv.testertool.ue;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.URISyntaxException;
import java.net.UnknownHostException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;

/**
 * UE Class that is used to simulate User Equipment. Attaches to 
 * the eNodeB and simulated HTTP send/receive
 *
 * @author ahmadarslan
 */

public class UE implements Runnable
{
	private static final Logger logger = LoggerFactory.getLogger("UELogger");

	private UEControlInterface ueControlInterface;
	UEParameters UEParameters;
	private XMLParser xmlparser;
	
	private UEController uEController;
	private String eNBUES1APID;
	
	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}
	
	public UE(int id, UEParameters UEParams, XMLParser xmlparser, UEController uEController)
	{
		UEParameters = UEParams;
		ueControlInterface = new UEControlInterface();
	
		this.eNBUES1APID = Integer.toHexString(id);
		//this.eNBUES1APID = Integer.toString(id);
		
		if(eNBUES1APID.length() == 3)
			eNBUES1APID = "0" + eNBUES1APID;
		if(eNBUES1APID.length() == 2)
			eNBUES1APID = "00" + eNBUES1APID;
		if(eNBUES1APID.length() == 1)
			eNBUES1APID = "000" + eNBUES1APID;
		
		//System.out.println(eNBUES1APID);
		
		this.uEController = uEController;
		this.xmlparser = xmlparser;
	}
	
	private String pdnipv4; // Received from eNB via processAttach()
	
	public void processAttachResponse(String pdnipv4)
	{
		this.pdnipv4 = pdnipv4;
		
		/* HTTP Request code to go here */
		
		/*try
		{
			if(!pdnipv4.equals("attachfailure"))
			{
				Thread.sleep(2000);

				//for(int i=0;i<10;i++)		//Uncomment this line if you want to test N number of HTTP connections from a single UE
				{
					new Thread()
					{
						public void run()
						{
							HTTPClient httpClient = new HTTPClient();;
							try {
								httpClient.sendRequest(pdnipv4);
							} 
							catch (URISyntaxException | IOException e) {
								e.printStackTrace();
							}

						}
					}.start();
				}
			}
		}
		
		catch(InterruptedException e)
		{
			e.printStackTrace();
		}*/
	}
	
	public Logger getLogger()
	{
		return UE.logger;
	}
	
	@Override
	public void run()
	{
		//logger.info("UE " + id + " started");
		uEController.sendAttachRequest(this);

		/* Send Attach command to eNB for attaching to the MME */
		//String pdnipv4 = ueControlInterface.sendAttachRequest("Attach;" + UEParameters.toString(), xmlparser.geteNBIP(), xmlparser.geteNBPort());
	}
}
