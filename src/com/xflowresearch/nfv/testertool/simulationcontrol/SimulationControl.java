package com.xflowresearch.nfv.testertool.simulationcontrol;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.ue.UE;

/**
 * SimulationControl
 * 
 *	Simulation Control class responsible for reading the input
 *	parameters of the simulation from a file and based on the 
 *	config parameters, it spawns the UE and eNodeB threads.
 *
 * 
 * @author ahmadarslan
 */
public class SimulationControl 
{
	private static SimulationControl instance = new SimulationControl();

	private eNodeB enodeb;
	private UE ue;
	
	private XMLParser xmlparser;

	/** Logger to log the messages and Errors **/
	private static final Logger logger = LoggerFactory.getLogger("SimulationControlLogger");

	
	private SimulationControl(){
		enodeb = new eNodeB();
		ue = new UE();

		xmlparser = new XMLParser();
	}

	
	public static SimulationControl getInstance( ) {
		return instance;
	}
	
	
	public Logger getLogger(){
		return SimulationControl.logger;
	}


	public void startSimulation(){
		logger.info("Simulation started");

		/*TODO: Parse/Read the input parameters from 'XML' files here!! */
		xmlparser.readSimulationParameters();

		/** Initialize UE and eNodeB instances' data and start their threads**/
		enodeb.setXMLParser(xmlparser);
		Thread eNBThread = new Thread(enodeb);
		eNBThread.setName("eNBThread1");
		eNBThread.start();

		Thread UEThread = new Thread(ue);
		UEThread.setName("UEThread1");
		UEThread.start();

	}

}