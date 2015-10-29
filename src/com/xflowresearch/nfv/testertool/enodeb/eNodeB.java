package com.xflowresearch.nfv.testertool.enodeb;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1u.GTP;

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
	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");
	
	private XMLParser xmlparser;
	
	public void setXMLParser(XMLParser xmlparser){
		this.xmlparser = xmlparser;
	}

	public eNodeB(){

	}


	public Logger getLogger(){
		return eNodeB.logger;
	}


	@Override
	public void run() {
		
		logger.info("eNodeB started");

		/** Test Attach Sequence initiation **/
		AttachSimulator as = new AttachSimulator(xmlparser);
		GTP simulateUserTraffic = new GTP();
	
		/**
		 * establish s1 signalling with the MME
		 */
		if(as.establishS1Signalling(xmlparser)){
			logger.info("S1Signalling established with MME");
			
			
			/**
			 * Start the attach sequence with the MME for a UE
			 */
			as.initiateAttachSequence(xmlparser);
			
			
			try 
			{
				Thread.sleep(2000);
			} 
			catch (InterruptedException e) {
				e.printStackTrace();
			}
			
			
			/**
			 * Simulate HTTP Traffic towards S-GW
			 */
			simulateUserTraffic.simulateGTPEchoRequest(as.getTransportLayerAddress(), 
					as.getPDNIpv4(), 
					as.getTEID());
		}
		else{
			logger.error("Unable to establish S1Signalling with MME");
		}
		
	}



	
	
}
