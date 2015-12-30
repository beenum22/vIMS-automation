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
import com.xflowresearch.nfv.testertool.ue.UEParameter;

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
	private int UEThreadSpawnDelay;
	private String APN;
	
	private int eNBCount;
	private String eNBIP;
	private String eNBPort;

	public int getUEThreadSpawnDelay()
	{
		return UEThreadSpawnDelay;
	}
	
	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}
	
	public String geteNBIP()
	{
		return eNBIP;
	}
	
	public String geteNBPort()
	{
		return eNBPort;
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
	
	private String MCC, MNC;
	
	public String getPLMN()
	{
		try
		{
			if(MNC.length() == 2)
			{
				MNC = MNC + "f";
			}
			
			char [] MCCArray = MCC.toCharArray();
			char [] MNCArray = MNC.toCharArray();
			char [] PLMNArray = new char[6];
			
			PLMNArray[0] = MCCArray[1];
			PLMNArray[1] = MCCArray[0];
			PLMNArray[2] = MNCArray[2];
			PLMNArray[3] = MCCArray[2];
			PLMNArray[4] = MNCArray[1];
			PLMNArray[5] = MNCArray[0];
			
			return new String(PLMNArray);
		}
		
		catch(NullPointerException npe)
		{
			System.out.println("Null Pointer Exception while computing PLMN. Check if MCC/MNC are null.");
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
		
		return null;
	}	
	
	public String getAPN()
	{
		return APN;
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

				if(item.getName().equals("MCC"))
				{
					MCC = item.getText();
				}
				
				else if(item.getName().equals("MNC"))
				{
					MNC = item.getText();
				}
				
				if(item.getName().equals("SimulationParams"))
				{
					UECount = Integer.parseInt(item.getChild("UECount").getText());
					//UEThreadSpawnDelay = Integer.parseInt(item.getChild("UEThreadSpawnDelay").getText());
					eNBCount = Integer.parseInt(item.getChild("eNBCount").getText());
					MMEIP = item.getChild("MMEIP").getText();
					MMEPort = item.getChild("MMEPort").getText();
				}

				if(item.getName().equals("UEParams"))
				{
					eNBUES1APID = item.getChild("eNBUES1APID").getText();
					
					TAI = item.getChild("TAI").getText();
					TAI = new StringBuilder(TAI).insert(2, getPLMN()).toString();
					//System.out.println("TAI: " + TAI);
					
					EUTRANCGI = item.getChild("EUTRANCGI").getText();
					EUTRANCGI = new StringBuilder(EUTRANCGI).insert(2, getPLMN()).toString();
					//System.out.println("EUTRANCGI: " + EUTRANCGI);
					
					RRCEstablishmentCause = item.getChild("RRCEstablishmentCause").getText();
					
					APN = item.getChild("APN").getText();
					System.out.println(APN);
				}

				if(item.getName().equals("eNBParams"))
				{
					eNBIP = item.getChild("eNBIP").getText();
					eNBPort = item.getChild("eNBPort").getText();
				}

				if(item.getName().equals("S1SignallingParams"))
				{
					s1signallingParams.GlobalENBID = item.getChild("GlobalENBID").getText();
					s1signallingParams.GlobalENBID = new StringBuilder(s1signallingParams.GlobalENBID).insert(2, getPLMN()).toString();
					//System.out.println("GlobalENBID: " + s1signallingParams.GlobalENBID);
					
					s1signallingParams.eNBname = item.getChild("eNBname").getText();
					
					s1signallingParams.SupportedTAs = item.getChild("SupportedTAs").getText();
					s1signallingParams.SupportedTAs = new StringBuilder(s1signallingParams.SupportedTAs).insert(8, getPLMN()).toString();
					//System.out.println("SupportedTAs: " + s1signallingParams.SupportedTAs);
					
					s1signallingParams.DefaultPagingDRX = item.getChild("DefaultPagingDRX").getText();
				}

				if(item.getName().equals("AuthenticationResponseParams"))
				{
					authenticationResponseParams.EUTRANCGI = item.getChild("EUTRANCGI").getText();
					authenticationResponseParams.EUTRANCGI = new StringBuilder(authenticationResponseParams.EUTRANCGI).insert(2, getPLMN()).toString();
					//System.out.println("EUTRANCGI: " + authenticationResponseParams.EUTRANCGI);

					
					authenticationResponseParams.TAI = item.getChild("TAI").getText();
					authenticationResponseParams.TAI= new StringBuilder(authenticationResponseParams.TAI).insert(2, getPLMN()).toString();
					//System.out.println("TAI: " + authenticationResponseParams.TAI);
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
