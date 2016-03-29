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
import com.xflowresearch.nfv.testertool.ue.UEParameters;

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

	private String MCC, MNC;
	private String TAI;
	private String EUTRANCGI;
	private String RRCEstablishmentCause;

	private String MMEIP;
	private String MMEPort;

	private int UECount;
	private String APN;
	
	private int eNBCount;
	
	private String WebServerIP;
	
	public String getWebServerIP()
	{
		return WebServerIP;
	}
	
	private int numberOfHttpRequests = 0;
	
	public int getNumberOfHttpRequests()
	{
		return numberOfHttpRequests;
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

	private ArrayList <UEParameters>  mUEParameters = new ArrayList <UEParameters> ();
	public UEParameters getUEParameters(int index)
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
    				mUEParameters.add(new UEParameters(item.getChild("IMSI").getText(), item.getChild("K").getText()));
    		}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
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
			npe.printStackTrace();
			return null;
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
			return null;
		}
	}	
	
	public String getAPN()
	{
		return APN;
	}

	public String convertIpToHex(String IP)
	{
		//String IP = "192.168.42.72";

		String[] chunks = IP.split("\\.");

		long sum = 0;
		for (int i = 0, j = chunks.length - 1; i < chunks.length; i++, j--)
		{
			//System.out.println(Integer.parseInt(chunks[i]) + " * 256 ^ " + j);
			sum += Integer.parseInt(chunks[i]) * (long)Math.pow(256, j);
			//System.out.println(Integer.parseInt(chunks[i]) + " * " + Math.pow(256, j));
		}

		return Long.toHexString(sum); //new String(sum); //System.out.println(sum);
	}
	
	private String returnAddress;
	
	public String getReturnIpInHex()
	{
		return convertIpToHex(returnAddress);
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
					eNBCount = Integer.parseInt(item.getChild("eNBCount").getText());
					MMEIP = item.getChild("MMEIP").getText();
					MMEPort = item.getChild("MMEPort").getText();
				}

				if(item.getName().equals("UEParams"))
				{
					TAI = item.getChild("TAI").getText();
					TAI = new StringBuilder(TAI).insert(2, getPLMN()).toString();
					//System.out.println("TAI: " + TAI);
					
					EUTRANCGI = item.getChild("EUTRANCGI").getText();
					EUTRANCGI = new StringBuilder(EUTRANCGI).insert(2, getPLMN()).toString();
					EUTRANCGI += convertIpToHex(item.getChildText("returnIP"));
					
					returnAddress = item.getChildText("returnIP");
					
					//returnIP = item.getChildText("returnIP");
					//System.out.println("EUTRANCGI: " + EUTRANCGI);
					
					RRCEstablishmentCause = item.getChild("RRCEstablishmentCause").getText();
					
					APN = item.getChild("APN").getText();
					WebServerIP = item.getChildText("WebServerIP");
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
		}
		
		catch(IOException ioe)
		{
			// print the exception and log it in simulation control logger.
			ioe.printStackTrace();
		}
	}
}
