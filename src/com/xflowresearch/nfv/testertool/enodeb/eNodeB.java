package com.xflowresearch.nfv.testertool.enodeb;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * eNodeB
 * 
 *	eNodeB class that executes on the eNodeB thread
 *	and initiates the eNodeB functionality.
 *
 * 
 * @author ahmadarslan
 */
public class eNodeB implements Runnable
{
	private static eNodeB instance = new eNodeB();

	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");


	private eNodeB(){

	}


	public static eNodeB getInstance() {
		return instance;
	}


	public Logger getLogger(){
		return eNodeB.logger;
	}


	@Override
	public void run() {
		
		logger.info("eNodeB started");

		/** Test Attach Sequence initiation **/
		AttachSimulator as = new AttachSimulator();
		as.s1apTestPacket();
		
	}



	
	
}
