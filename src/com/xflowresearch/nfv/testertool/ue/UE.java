package com.xflowresearch.nfv.testertool.ue;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UE implements Runnable
{
	private static UE instance = new UE();
	
	private static final Logger logger = LoggerFactory.getLogger("UELogger");

	
	private UE(){

	}
	

	public static UE getInstance( ) {
		return instance;
	}
	
	
	public Logger getLogger(){
		return UE.logger;
	}
	
	
	@Override
	public void run() {
		// TODO Auto-generated method stub
		
		logger.info("UE started");
		
	}

}
