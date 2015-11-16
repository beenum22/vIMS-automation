package com.xflowresearch.nfv.testertool.ue;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * UE
 * 
 *	UE class that executes on the eNodeB thread
 *	and initiates the UE functionality.
 *
 * 
 * @author ahmadarslan
 */
public class UE implements Runnable
{
	private static final Logger logger = LoggerFactory.getLogger("UELogger");

	
	private UEControlInterface ueControlInterface;

	public UE(){
		ueControlInterface = new UEControlInterface();
	}


	public Logger getLogger(){
		return UE.logger;
	}


	@Override
	public void run() {
		// TODO Auto-generated method stub
		logger.info("UE started");
		ueControlInterface.sendControlCommand("Attach;UEParams");
	}

}
