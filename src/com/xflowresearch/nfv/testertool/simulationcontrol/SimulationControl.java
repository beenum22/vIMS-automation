package com.xflowresearch.nfv.testertool.simulationcontrol;

import java.util.ArrayList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.ue.UE;
import com.xflowresearch.nfv.testertool.ue.UEController;

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
	private static SimulationControl instance = null;// = new SimulationControl();

	//private eNodeB enodeb;
	//private UE ue;
	private ArrayList <Thread> UEs;
	private ArrayList <Thread> eNBs;
	
	private UEController uEController;

	private XMLParser xmlparser;

	/** Logger to log the messages and Errors **/
	private static final Logger logger = LoggerFactory.getLogger("SimulationControlLogger");

	private SimulationControl()
	{
		//enodeb = new eNodeB();
		//ue = new UE();
		
		UEs = new ArrayList<Thread>();
		eNBs = new ArrayList<Thread>();
		
		xmlparser = new XMLParser();
		uEController = new UEController(xmlparser);
	}
	
	/** Get the Simulation Controller instance */
	public static SimulationControl getInstance()
	{
		try
		{
			if(instance == null)
			{
				instance = new SimulationControl();
				return instance;
			}
			
			else
			{		
				return instance;
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
			return null;
		}
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
			int eNBCount = xmlparser.geteNBCount();
			
			for(int i = 0; i <eNBCount; i++)
			{
				eNodeB temp = new eNodeB(xmlparser);
				
				eNBs.add(new Thread(temp));
				eNBs.get(i).setName("eNodeB" + i);
				eNBs.get(i).start();
				logger.info("eNodeB" + i + " Thread Spawned");
			}
		}
		
		if(xmlparser.getUECount() != 0)
		{
			uEController.initENBConnection();			
			uEController.spawnReceiverThread();
			
			int UECount = xmlparser.getUECount();
			
			for(int i = 0; i < UECount; i++)
			{
				if(i != 0 && i % 200 == 0)
				{
					try
					{
						Thread.sleep(xmlparser.getSpawnDelay());
					}
					
					catch(Exception exc)
					{
						exc.printStackTrace();
					}
				}
				
				UEs.add(new Thread(new UE(i, xmlparser.getUEParameters(i), xmlparser, uEController)));
				UEs.get(i).setName("UEThread" + i);
				logger.info("UE Thread" + i + " Spawned");
				UEs.get(i).start();
			}
		}
	}
}