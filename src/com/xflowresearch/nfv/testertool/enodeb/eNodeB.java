package com.xflowresearch.nfv.testertool.enodeb;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.UserControlInterface;
import com.xflowresearch.nfv.testertool.enodeb.s1u.GTP;
import com.xflowresearch.nfv.testertool.enodeb.s1u.UserDataInterface;

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
	
	private SctpClient sctpClient;
	private UserDataInterface userDataInterface;
	private UserControlInterface userControlInterface;

	public eNodeB(){
		sctpClient = new SctpClient();
		userDataInterface = new UserDataInterface();
		userControlInterface = new UserControlInterface();
	}

	public void setXMLParser(XMLParser xmlparser){
		this.xmlparser = xmlparser;
	}
	public Logger getLogger(){
		return eNodeB.logger;
	}


	@Override
	public void run() 
	{
		logger.info("eNodeB started");

		/** Test Attach Sequence initiation **/
		AttachSimulator as = new AttachSimulator(xmlparser);
		GTP gtpEcho = new GTP();
		
		
		
		/**
		 * establish s1 signalling with the MME
		 */
		if(as.establishS1Signalling(xmlparser, sctpClient))
		{
			logger.info("S1 Signaling Successfully Established");
			
			/** Listen for UE Commands for Control Plane Signaling **/
			userControlInterface.listenForUserControlCommands();
			
			/** Listen for UE Data for User Plane **/
			userDataInterface.listenForUserDataTraffic();
			
			
			/**
			 * Start the attach sequence with the MME for a UE
			 */
			if(as.initiateAttachSequence(xmlparser))
			{
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
				gtpEcho.simulateGTPEchoRequest(as.getTransportLayerAddress(), 
						as.getPDNIpv4(), 
						as.getTEID());
			}
		}
		else{
			logger.error("Unable to establish S1Signalling with MME");
		}
	}
}
