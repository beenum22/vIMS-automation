package com.xflowresearch.nfv.testertool.ue;

import java.io.IOException;
import java.net.URISyntaxException;
import java.net.UnknownHostException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;

/**
 * UE
 * 
 * UE class that executes on the eNodeB thread and initiates the UE
 * functionality.
 *
 * @author ahmadarslan
 */
public class UE implements Runnable
{
	private static final Logger logger = LoggerFactory.getLogger("UELogger");

	private UEControlInterface ueControlInterface;
	private HTTPClient httpClient;
	UEParameter UEParameters;
	private XMLParser xmlparser;

	public UE(UEParameter UEParams, XMLParser xmlparser)
	{
		UEParameters = UEParams;
		ueControlInterface = new UEControlInterface();
		httpClient = new HTTPClient();
		
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

		/* Send Attach command to eNB for attaching to the MME!! to the MME */
		String pdnipv4 = ueControlInterface.sendControlCommand("Attach;" + UEParameters.toString(), xmlparser.geteNBIP()); /* UEParams = IMSI + K?" */

		try
		{
			if( !pdnipv4.equals("attachfailure"))
			{
				Thread.sleep(3000);
				httpClient.sendRequest(pdnipv4);
			}
		}

		catch(UnknownHostException e)
		{
			e.printStackTrace();
		}

		catch(URISyntaxException e)
		{
			e.printStackTrace();
		}

		catch(IOException e)
		{
			e.printStackTrace();
		}

		catch(InterruptedException e)
		{
			e.printStackTrace();
		}
	}
}
