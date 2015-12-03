package com.xflowresearch.nfv.testertool.simulationcontrol;

import java.util.ArrayList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.ue.UE;

/**
 * SimulationControl
 * 
 * Simulation Control class responsible for reading the input parameters of the
 * simulation from a file and based on the config parameters, it spawns the UE
 * and eNodeB threads.
 *
 * 
 * @author ahmadarslan
 */

public class SimulationControl
{	
	private static SimulationControl instance = new SimulationControl();

	private eNodeB enodeb;
	private UE ue;
	private ArrayList <Thread> UEs;

	private XMLParser xmlparser;

	/** Logger to log the messages and Errors **/
	private static final Logger logger = LoggerFactory.getLogger("SimulationControlLogger");

	private SimulationControl()
	{
		enodeb = new eNodeB();
		//ue = new UE();
		UEs = new ArrayList<Thread>();

		xmlparser = new XMLParser();
	}
	
	/** Get the Simulation Controller instance */
	public static SimulationControl getInstance()
	{
		return instance;
	}

	/** Get the logger instance */
	public Logger getLogger()
	{
		return SimulationControl.logger;
	}
	
	/** Start the simulation */	
	public void startSimulation()
	{
		logger.info("Simulation started");

		/* Parse/Read the input parameters from 'XML' files here!! */
		xmlparser.readSimulationParameters();
		xmlparser.readIMSIParamters();

		/* Initialize UE and eNodeB instances' data and start their threads */
		if(xmlparser.geteNBCount() != 0)
		{
			enodeb.setXMLParser(xmlparser);
			Thread eNBThread = new Thread(enodeb);
			eNBThread.setName("eNBThread1");
			eNBThread.start();
			logger.info("eNodeB Thread Spawned");
		}

		if(xmlparser.getUECount() != 0)
		{
			int UECount = xmlparser.getUECount();
			
			for(int i = 0; i < UECount; i++)
			{
				UEs.add(new Thread(new UE(xmlparser.getUEParameters(i))));
				UEs.get(i).setName("UEThread"+i);
				logger.info("UE Thread " + i + " Spawned");
				UEs.get(i).start();
			}
			
			/*Thread UEThread = new Thread(ue);
			UEThread.setName("UEThread1");
			UEThread.start();
			logger.info("UE Thread Spawned");*/
		}
	}
}