package testing;


import java.io.File;

import com.xflowresearch.nfv.testertool.simulationcontrol.SimulationControl;

public class main {

	public static void main(String[] args) 
	{

		/** Delete logs from previous launches **/ 
		File index = new File("logs");
		String[]entries = index.list();

		if(entries != null)
		{
			for(String s: entries){
				File currentFile = new File(index.getPath(),s);
				currentFile.delete();
			}
		}
		SimulationControl.getInstance().startSimulation();
	}
}
