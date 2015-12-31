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
	UEParameter UEParameters;
	private XMLParser xmlparser;

	public UE(UEParameter UEParams, XMLParser xmlparser)
	{
		UEParameters = UEParams;
		ueControlInterface = new UEControlInterface();

		this.xmlparser = xmlparser;
	}

	public Logger getLogger()
	{
		return UE.logger;
	}

	@Override
	public void run()
	{
		logger.info("UE started");

		/* Send Attach command to eNB for attaching to the MME */
		String pdnipv4 = ueControlInterface.sendAttachRequest("Attach;" + UEParameters.toString(), xmlparser.geteNBIP(), xmlparser.geteNBPort());

		try
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
		}
	}
}
