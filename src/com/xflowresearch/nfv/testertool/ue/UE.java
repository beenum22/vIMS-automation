package com.xflowresearch.nfv.testertool.ue;

import java.io.IOException;
import java.net.URISyntaxException;
import java.net.UnknownHostException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * UE
 * 
 *	UE class that executes on the eNodeB thread
 *	and initiates the UE functionality.
 *
 * @author ahmadarslan
 */
public class UE implements Runnable
{
	private static final Logger logger = LoggerFactory.getLogger("UELogger");

	
	private UEControlInterface ueControlInterface;
	private HTTPClient httpClient;

	public UE(){
		ueControlInterface = new UEControlInterface();
		httpClient = new HTTPClient();
	}


	public Logger getLogger(){
		return UE.logger;
	}


	@Override
	public void run() {
		// TODO Auto-generated method stub
		logger.info("UE started");
		
		/** Send Attach command to eNB for attaching to the MME!! to the MME **/
		String pdnipv4 = ueControlInterface.sendControlCommand("Attach;UEParams");
		
		try {
			Thread.sleep(3000);
			httpClient.sendRequest(pdnipv4);
		} catch (UnknownHostException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (URISyntaxException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
	}

}
