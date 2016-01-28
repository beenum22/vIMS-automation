package testing;

import java.io.File;

import com.xflowresearch.nfv.testertool.common.IMSIParser;
import com.xflowresearch.nfv.testertool.simulationcontrol.SimulationControl;

public class Run
{
	public static void main(String [] args)
	{
		/* Delete logs from previous launches **/
		File index = new File("logs");
		String [] entries = index.list();
		
		/*IMSIParser parser = new IMSIParser();
		parser.createIMSIFile("../data.txt", "configuration/IMSIParameters.xml");*/
		
		if(entries != null)
		{
			for(String s:entries)
			{
				File currentFile = new File(index.getPath(), s);
				currentFile.delete();
			}
		}
		
		SimulationControl inst = SimulationControl.getInstance();
		
		if(inst != null)
		{
			inst.startSimulation();
		}
		
		else
		{
			System.out.println("Failed to initialize Simulation Control Instance");
		}
	}
}
