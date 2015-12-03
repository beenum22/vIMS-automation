package com.xflowresearch.nfv.testertool.common;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;

import com.xflowresearch.nfv.testertool.simulationcontrol.SimulationControl;
import com.xflowresearch.nfv.testertool.simulationcontrol.UEParameter;

/**
 * XMLParser
 * 
 * XMLParser class for parsing the input/config parameters from xml files.
 * 
 * @author ahmadarslan
 */
public class XMLParser
{		
	public class S1SignallingParams
	{
		public String GlobalENBID;
		public String eNBname;
		public String SupportedTAs;
		public String DefaultPagingDRX;
	}

	private S1SignallingParams s1signallingParams = new S1SignallingParams();

	public class AuthenticationResponseParams
	{
		public String EUTRANCGI;
		public String TAI;
	}

	private AuthenticationResponseParams authenticationResponseParams = new AuthenticationResponseParams();

	private String eNBUES1APID;
	private String TAI;
	private String EUTRANCGI;
	private String RRCEstablishmentCause;

	private String MMEIP;
	private String MMEPort;

	private int UECount;
	private int eNBCount;

	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}

	public String getTAI()
	{
		return TAI;
	}

	public String getEUTRANCGI()
	{
		return EUTRANCGI;
	}

	public String getRRCEstablishmentCause()
	{
		return RRCEstablishmentCause;
	}

	public String getMMEIP()
	{
		return MMEIP;
	}

	public String getMMEPort()
	{
		return MMEPort;
	}

	public S1SignallingParams getS1signallingParams()
	{
		return s1signallingParams;
	}

	public AuthenticationResponseParams getAuthenticationResponseParams()
	{
		return authenticationResponseParams;
	}

	public int getUECount()
	{
		return UECount;
	}

	public int geteNBCount()
	{
		return eNBCount;
	}

	private ArrayList <UEParameter>  mUEParameters = new ArrayList <UEParameter> ();
	public UEParameter getUEParameters(int index)
	{
		return mUEParameters.get(index);
	}
	
	public void readIMSIParamters()
	{
		try
		{
    		File inputFile = new File("configuration/IMSIParameters.xml");
    		
    		SAXBuilder saxBuilder = new SAXBuilder();
    		
    		Document document = saxBuilder.build(inputFile);
    		
    		Element rootElement = document.getRootElement();
    		
    		List <Element> items = rootElement.getChildren();
    		
    		for(Element item:items)
    		{
    			//System.out.println(item.getName());
    			if(item.getName().equals("Value"))
    				mUEParameters.add(new UEParameter(item.getChild("IMSI").getText(), item.getChild("K").getText()));
    		}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	public void readSimulationParameters()
	{
		try
		{
			File inputFile = new File("configuration/SimulationParameters.xml");

			SAXBuilder saxBuilder = new SAXBuilder();

			Document document = saxBuilder.build(inputFile);

			Element classElement = document.getRootElement();

			List <Element> itemList = classElement.getChildren();

			for(int temp = 0; temp < itemList.size(); temp++)
			{
				Element item = itemList.get(temp);

				if(item.getName().equals("SimulationParams"))
				{
					UECount = Integer.parseInt(item.getChild("UECount").getText());
					eNBCount = Integer.parseInt(item.getChild("eNBCount").getText());
					MMEIP = item.getChild("MMEIP").getText();
					MMEPort = item.getChild("MMEPort").getText();
				}

				if(item.getName().equals("UEParams"))
				{
					eNBUES1APID = item.getChild("eNBUES1APID").getText();
					TAI = item.getChild("TAI").getText();
					EUTRANCGI = item.getChild("EUTRANCGI").getText();
					RRCEstablishmentCause = item.getChild("RRCEstablishmentCause").getText();
				}

				if(item.getName().equals("eNBParams"))
				{

				}

				if(item.getName().equals("S1SignallingParams"))
				{
					s1signallingParams.GlobalENBID = item.getChild("GlobalENBID").getText();
					s1signallingParams.eNBname = item.getChild("eNBname").getText();
					s1signallingParams.SupportedTAs = item.getChild("SupportedTAs").getText();
					s1signallingParams.DefaultPagingDRX = item.getChild("DefaultPagingDRX").getText();
				}

				if(item.getName().equals("AuthenticationResponseParams"))
				{
					authenticationResponseParams.EUTRANCGI = item.getChild("EUTRANCGI").getText();
					authenticationResponseParams.TAI = item.getChild("TAI").getText();
				}
			}
		}
		catch(JDOMException e)
		{
			// print the exception and log it in simulation control logger.
			e.printStackTrace();
			SimulationControl.getInstance().getLogger().error("", e.toString());
		}
		catch(IOException ioe)
		{
			// print the exception and log it in simulation control logger.
			ioe.printStackTrace();
			SimulationControl.getInstance().getLogger().error(ioe.toString());
		}
	}

}
