package com.xflowresearch.nfv.testertool.enodeb;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class eNodeB implements Runnable
{
	private static eNodeB instance = new eNodeB();
	
	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");


	private eNodeB(){

	}
	

	public static eNodeB getInstance( ) {
		return instance;
	}
	
	
	public Logger getLogger(){
		return eNodeB.logger;
	}
	
	
	@Override
	public void run() {
		// TODO Auto-generated method stub
		
		logger.info("eNodeB started");
		
	}

}
