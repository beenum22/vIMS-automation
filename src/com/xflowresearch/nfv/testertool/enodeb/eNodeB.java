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

		AttachSimulator as  = new AttachSimulator(xmlparser);
		/**
		 * establish s1 signalling with the MME
		 */
		if(as.establishS1Signalling(xmlparser, sctpClient))
		{
			logger.info("S1 Signaling Successfully Established");
			
			/** Listen for UE Commands for Control Plane Signaling **/
			userControlInterface.listenForUserControlCommands(xmlparser, as);
			
			/** Listen for UE Data for User Plane **/
			userDataInterface.listenForUserDataTraffic();
			
			
			/**
			 * Start the attach sequence with the MME for a UE
			 */
			
		}
		else{
			logger.error("Unable to establish S1Signalling with MME");
		}
	}
}
