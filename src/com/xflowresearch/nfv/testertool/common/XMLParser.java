package com.xflowresearch.nfv.testertool.common;

import java.io.File;
import java.io.IOException;
import java.util.List;

import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;

import com.xflowresearch.nfv.testertool.simulationcontrol.SimulationControl;

public class XMLParser {

	public void readSimulationParameters()
	{
		try 
		{
			File inputFile = new File("configuration/SimulationParameters.xml");

			SAXBuilder saxBuilder = new SAXBuilder();

			Document document = saxBuilder.build(inputFile);

			Element classElement = document.getRootElement();

			List<Element> itemList = classElement.getChildren();

			for (int temp = 0; temp < itemList.size(); temp++) 
			{    
				Element item = itemList.get(temp);
				
				if(item.getName().equals("SimulationParams"))
				{
					System.out.println("UECount: " + item.getChild("UECount").getText());
					System.out.println("eNBCount: "+ item.getChild("eNBCount").getText());
				}
				if(item.getName().equals("UEParams"))
				{
					System.out.println("IMSI: " + item.getChild("IMSI").getText());
					System.out.println("IMEI: "+ item.getChild("IMEI").getText());
				}
				if(item.getName().equals("eNBParams"))
				{
					System.out.println("eNBID: " + item.getChild("eNBID").getText());
					System.out.println("TAC: "+ item.getChild("TAC").getText());
					System.out.println("MNC: " + item.getChild("MNC").getText());
					System.out.println("MCC: "+ item.getChild("MCC").getText());
					System.out.println("MMEI: "+ item.getChild("MMEI").getText());
				}
				System.out.println();        		
			}
		}
		catch(JDOMException e)
		{
			//print the exception and log it in simulation control logger.
			e.printStackTrace();
			SimulationControl.getInstance().getLogger().error("", e.toString());
		}
		catch(IOException ioe)
		{
			//print the exception and log it in simulation control logger.
			ioe.printStackTrace();
			SimulationControl.getInstance().getLogger().error(ioe.toString());
		}
	}

}
