package com.xflowresearch.nfv.testertool.simulationcontrol;

import java.util.ArrayList;

import com.xflowresearch.nfv.testertool.common.ConfigHandler;
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
 * @author ahmadarslan, Aamir Khan
 */

public class SimulationControl
{
	private static SimulationControl instance = null;
	
	private ArrayList<Thread> UEs;
	private ArrayList<Thread> eNBs;
	private ArrayList<eNodeB> enodeBs;

	private UEController uEController;

	private ConfigHandler xmlparser;

	/** Logger to log the messages and Errors **/
	// private static final Logger logger =
	// LoggerFactory.getLogger("SimulationControlLogger");
	
	private SimulationControl()
	{
		UEs = new ArrayList<Thread>();
		eNBs = new ArrayList<Thread>();
		enodeBs = new ArrayList<eNodeB>();

		xmlparser = new ConfigHandler();
		uEController = new UEController(xmlparser, enodeBs);
		uEController.startGtpListener();
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

		catch (Exception exc)
		{
			exc.printStackTrace();
			return null;
		}
	}

	/** Get the logger instance */
	/*
	 * public Logger getLogger() { return SimulationControl.logger; }
	 */

	/** Start the simulation */
	public void startSimulation(int noOfUEs, int noOfeNBs)
	{
		try
		{
			// logger.info("Simulation started");

			/* Parse/Read the input parameters from 'XML' files here!! */
			xmlparser.readSimulationParameters();
			//xmlparser.readIMSIParamters();

			/*
			 * Initialize UE and eNodeB instances' data and start their threads
			 */

			int eNBCount = noOfeNBs;

			for (int i = 0; i < eNBCount; i++)
			{
				eNodeB temp = new eNodeB(xmlparser, uEController);
				
				enodeBs.add(temp);
				//new Thread(enodeBs.get(i)).start();
			}

			Thread.sleep(1000);

			int UECount = noOfUEs; //xmlparser.getUECount();

			for (int i = 0; i < UECount; i++)
			{
				//UEs.add(new Thread(new UE(i, xmlparser.getUEParameters(i), xmlparser, uEController)));
				UEs.get(i).setName("UEThread" + i);
				// logger.info("UE Thread" + i + " Spawned");
				UEs.get(i).start();
			}
		}

		catch (Exception exc)
		{
			exc.printStackTrace();
		}
	}
}