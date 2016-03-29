package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.io.ObjectOutputStream;
import java.math.BigInteger;
import java.net.InetAddress;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.regex.Pattern;

import javax.xml.bind.DatatypeConverter;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.Value;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.enodeb.s1u.User;
import com.xflowresearch.nfv.testertool.ue.UEController;
import com.xflowresearch.nfv.testertool.ue.nas.AttachSeqDemo;

public class UserCommandHandler implements Runnable
{
	private String TEID;
	private InetAddress transportLayerAddress;
	private InetAddress PDNIpv4;
	
	/* ---------------- State Variables ---------------- */
	
	private boolean authentication = false;
	private boolean securityMode = false;
	private boolean ESMInformationRequest = false;
	private boolean initialContextSetup = false;
	
	/* ------------------------------------------------- */
	
	private Socket socket;
	private eNodeB enodeb;
	private XMLParser xmlparser;
	
	//private AttachSimulator attachSimulator;
	
	private SctpClient sctpClient;
	
	private Object eNodeBLock;
	
	private ObjectOutputStream OOS;
	
	private String command;
	private String eNBUES1APID;
	
	private UEController ueController;
	
	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}
	
	public UserCommandHandler(String eNBUES1APID, String command, eNodeB enodeb, XMLParser xmlparser, SctpClient sctpClient, Object eNodeBLock, UEController ueController)
	{		
		this.enodeb = enodeb;
		this.xmlparser = xmlparser;
		this.sctpClient = sctpClient;
		this.eNodeBLock = eNodeBLock;
		this.command = command;
		this.ueController = ueController;
		this.eNBUES1APID = eNBUES1APID;
	}
	
	public void onPacketReceived(S1APPacket receivedPacket)
	{		
		try
		{
			if(!authentication)
			{
				//System.out.println(eNBUES1APID + "received");
				if(receivedPacket.getProcCode().equals("downlinkNASTransport") && receivedPacket.getValues().size() == 3)
				{
					sendAuthenticationResponse(receivedPacket, receivedPacket.geteNBUES1APID());
					authentication = true;
				}
				
				else
				{
					System.out.println(receivedPacket.geteNBUES1APID() + ": Attach(1) failure");
				}
			}
			
			else if(authentication && !securityMode)
			{
				if(receivedPacket!=null && receivedPacket.getProcCode().equals("downlinkNASTransport") && receivedPacket.getValues().size() == 3)
				{
					sendSecurityModeComplete(receivedPacket);
					securityMode = true;
				}
				
				else
				{
					System.out.println(receivedPacket.geteNBUES1APID() + ": Attach(2) failure");
				}
			}
			
			else if(authentication && securityMode && !ESMInformationRequest)
			{
				if(receivedPacket.getProcCode().equals("downlinkNASTransport") && receivedPacket.getValues().size() == 3)
				{
					sendESMInformationResponse(receivedPacket);
					ESMInformationRequest = true;
				}
				
				else
				{
					System.out.println(receivedPacket.geteNBUES1APID() + ": Attach(3) failure");
					ueController.processAttachResponse(eNBUES1APID + ";attachfailure");
				}
			}
			
			else if(authentication && securityMode && ESMInformationRequest && !initialContextSetup)
			{
				if(receivedPacket.getProcCode().equals("InitialContextSetup") && receivedPacket.getValues().size() == 6)
				{
					extractGTPData(receivedPacket);
					sendInitialContextSetupResponse(receivedPacket);
					sendAttachComplete(receivedPacket);
					
					User user = new User();
					user.setTEID(TEID);
					user.setIP(PDNIpv4.toString().substring(1, PDNIpv4.toString().length()));
					user.seteNBUES1APID(receivedPacket.geteNBUES1APID());
					user.setTransportLayerAddress(transportLayerAddress);
					initialContextSetup = true;
					
					synchronized(eNodeBLock)
					{
						enodeb.setTransportLayerAddressInUserControlInterface(transportLayerAddress);	
						enodeb.setTransportLayerAddress(transportLayerAddress);
						enodeb.addNewUser(user);
					}
					
					ueController.processAttachResponse(eNBUES1APID + ";" + user.getIP());
				}

				else
				{
					System.out.println(receivedPacket.geteNBUES1APID() + ": Attach(4) failure");
					
					ueController.processAttachResponse(eNBUES1APID + ";attachfailure");
				}
			}
			
			else
			{
				System.out.println("Attach failure");
				
				ueController.processAttachResponse(eNBUES1APID + ";attachfailure");
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	@Override
	public void run()
	{		
		try
		{
			executeUECommand();
		}
		
		catch(Exception e)
		{
			e.printStackTrace();
		}	
	}
	
	public void executeUECommand()
	{
		if(command.split(";")[0].equals("Attach"))
		{
			String ueparams = command.split(";")[2] + ";" + command.split(";")[3];
			initAttachSequence(ueparams);
		}
		
		/*Cater for other commands here */
	}

	public void initAttachSequence(String ueparams)
	{			
		sendAttachRequest(ueparams);
	}
	
	public void sendAttachRequest(String ueparams)
	{
		try
		{
			////// NAS packet Generation////////////////////////////
			//String AttachArguments = "08091132547698214305e0e000000000050202d011d1";
			String AttachArguments = "08" + ueparams.split(";")[0] + "05e0e000000000050202d011d1";
			AttachSeqDemo obj = new AttachSeqDemo();
			String NASPDU = obj.SendAttachPack(AttachArguments);
			//////////////////////////////////
	
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("eNBUES1APID", "reject", eNBUES1APID));
			values.add(new Value("NASPDU", "reject", NASPDU));
			values.add(new Value("TAI", "reject", xmlparser.getTAI()));
			values.add(new Value("EUTRANCGI", "ignore", xmlparser.getEUTRANCGI()));
			values.add(new Value("RRCEstablishmentCause", "ignore", xmlparser.getRRCEstablishmentCause()));
	
			//S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "initialUEMessage", "ignore", values, false);
			sendS1APacket("InitiatingMessage", "initialUEMessage", "ignore", values, false);
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}

		//return recievedPacket;
	}

	/**
	 * The second packet of the attach sequence, the Authentication Response is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendAuthenticationResponse(S1APPacket authenticationRequest, String eNBUES1APID)
	{
		try
		{
			AttachSeqDemo obj = new AttachSeqDemo();
			// NAS PDU GENERATION
			String k  = "465B5CE8B199B49FAA5F0A2EE238A6BC"; // key
			String op = "1918b840195c97017228127009ca194e"; // op values
	
			String NASPDUInAuthentication = authenticationRequest.getValue("NASPDU");
	
			String NASPDUInAuthenticationRequest = NASPDUInAuthentication.substring(2);
			String r = obj.ParseAuthRequest(NASPDUInAuthenticationRequest); // Parse Authentication Request Message and obtain Rand value
	
			if(r != null)
			{
					//return null;
				
				//System.out.println("R Value:"+r);
				//
				// get the NAS response from the NAS classes!!
				String NASPDU = obj.SendAuthResp(r, k, op);
				// NASPDU=(NASPDU.length()/2) + NASPDU ;
				// System.out.println(NASPDU);
				
				ArrayList <Value> values = new ArrayList <Value>();
				values.add(new Value("MMEUES1APID", "reject", authenticationRequest.getValue("MMEUES1APID")));
				values.add(new Value("eNBUES1APID", "reject", eNBUES1APID));
				values.add(new Value("NASPDU", "reject", NASPDU));
				values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
				values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));
		
				//S1APPacket recievedPacket = 
				sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}

		//return recievedPacket;
	}

	/**
	 * The third packet of the attach sequence, the SecurityModeComplete packet
	 * is sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendSecurityModeComplete(S1APPacket securityModeCommand)
	{
		try
		{
			// NAS PDU GENERATION
			String NASPDUInSecurityModeCommand = securityModeCommand.getValue("NASPDU");
	
			// get the NAS response from the NAS classes!!
			String NASPDU = "08471136cdbe00075e";
			//////////////////////////////////
	
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("MMEUES1APID", "reject", securityModeCommand.getValue("MMEUES1APID")));
			values.add(new Value("eNBUES1APID", "reject", securityModeCommand.getValue("eNBUES1APID"))); // TODO
																										 // change
																										 // it
																										 // to
																										 // Dynamic!!!
			values.add(new Value("NASPDU", "reject", NASPDU));
			values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
			values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));
	
			//S1APPacket recievedPacket = 
			sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
	
			//return recievedPacket;
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	/**
	 * The fourth packet of the attach sequence, the ESMInformationResponse is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	
	public String getAPNString(String APN)
	{
		String [] tokens = APN.split(Pattern.quote("."));
		
		String temp = "";
		
		for(int i = 0; i < tokens.length; i++)
		{
			temp += getLength(tokens[i]);
			temp += convert(tokens[i]);
		}

		//System.out.println(temp);		

		return temp;
	}

	private String getLength(String token)
	{
		String length = Integer.toHexString(token.length());
		if(length.length() == 1)
		{
			length = "0" + length;
		}
		
		return length;
	}

	public String convert(String string)
	{
		String hex = String.format("%x", new BigInteger(1, string.getBytes()));
		return hex;
	}

	public void sendESMInformationResponse(S1APPacket esmInformationRequest)
	{
		try
		{
			// NAS PDU GENERATION
			String NASPDUInESMInformationRequest = esmInformationRequest.getValue("NASPDU");
	
			// get the NAS response from the NAS classes!!
			String NASPDU = "1d270f6cfb77010202da28";
			
			String hexAPN = getAPNString(xmlparser.getAPN());
					
			String hexAPNLength = Integer.toHexString(hexAPN.length()/2);
			
			if(hexAPNLength.length() == 1)
			{
				hexAPNLength = "0" + hexAPNLength;
			}
			
			NASPDU += hexAPNLength + hexAPN;
			//System.out.println(hexAPNLength + hexAPN);
			//////////////////////////////////
	
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("MMEUES1APID", "reject", esmInformationRequest.getValue("MMEUES1APID")));
			values.add(new Value("eNBUES1APID", "reject", esmInformationRequest.getValue("eNBUES1APID")));
			values.add(new Value("NASPDU", "reject", NASPDU));
			values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
			values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));
	
			//S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
			sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
			}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}

		//return recievedPacket;
	}
	
	/**
	 * The fifth packet of the attach sequence, the InitialContextSetupResponse
	 * is sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendInitialContextSetupResponse(S1APPacket initialContextSetupRequest)
	{
		try
		{
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("MMEUES1APID", "reject", initialContextSetupRequest.getValue("MMEUES1APID")));
			values.add(new Value("eNBUES1APID", "reject", initialContextSetupRequest.getValue("eNBUES1APID")));
			values.add(new Value("ERABSetupListCtxtSURes", "ignore", "000032400a0a1f" + xmlparser.getReturnIpInHex() + TEID));
	
			sendS1APacket("SuccessfulOutcome", "InitialContextSetup", "reject", values, false);
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	/**
	 * The sixth packet of the attach sequence, the AttachComplete packet is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendAttachComplete(S1APPacket initialContextSetupRequest)
	{
		try
		{
			// NAS PDU GENERATION
			// String NASPDUInInitialContextSetupRequest =
			// initialContextSetupRequest.getValue("NASPDU");
	
			// get the NAS response from the NAS classes!!
			String NASPDU = "0d27cd3c638302074300035200c2";
			//////////////////////////////////
	
			ArrayList <Value> values = new ArrayList <Value>();
			values.add(new Value("MMEUES1APID", "reject", initialContextSetupRequest.getValue("MMEUES1APID")));
			values.add(new Value("eNBUES1APID", "reject", initialContextSetupRequest.getValue("eNBUES1APID")));
			values.add(new Value("NASPDU", "reject", NASPDU));
			values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
			values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));
	
			sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	/**
	 * Function to generate and send any sort of s1AP Packet, packet controlled
	 * by the input parameters.. The return is the hex-encoded reply received
	 * from the MME..
	 * 
	 * @param type
	 * @param procCode
	 * @param criticality
	 * @param values
	 * @return reply
	 */
	public void sendS1APacket(String type, String procCode, String criticality, ArrayList <Value> values, Boolean recieve)
	{
		try
		{
			S1APPacket pac = new S1APPacket(type, procCode, criticality, values.size());
	
			for(int i = 0; i < values.size(); i++)
			{
				pac.addValue(values.get(i).typeOfValue, values.get(i).criticality, values.get(i).value.length() / 2,
						values.get(i).value);
			}
	
			pac.createPacket();
			byte [] message = pac.getBytePacket();
	
			sctpClient.sendProtocolPayload(message, 18);
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	public void extractGTPData(S1APPacket attachComplete)
	{		
		try
		{
			String value = attachComplete.getValue("ERABToBeSetupListCtxtSUReq");
			value = value.substring(24, value.length());
	
			String ip1 = value.substring(0, 8);
			TEID = value.substring(8, 16);
			String ip2 = value.substring(146, 154);
	
			try
			{
				transportLayerAddress = InetAddress.getByAddress(DatatypeConverter.parseHexBinary(ip1));
				PDNIpv4 = InetAddress.getByAddress(DatatypeConverter.parseHexBinary(ip2));
			}
			
			catch(UnknownHostException e)
			{
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}

//		logger.info("Data Extracted From ESM InformationResponse - TransportLayerAddress:" + transportLayerAddress + " PDNIPv4:" + PDNIpv4 + " TEID:" + TEID);
	}
}
