package com.xflowresearch.nfv.testertool.enodeb;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;

import javax.xml.bind.DatatypeConverter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.ue.nas.AttachSeqDemo;

/**
 * AttachSimulator class to establish s1 signaling with MME and initiating the
 * attach sequence for a UE with the MME..
 * 
 * @author Ahmad Arslan
 *
 */
public class AttachSimulator
{
	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");

	InetAddress transportLayerAddress;
	InetAddress PDNIpv4;
	String TEID;

	private SctpClient sctpClient;
	private XMLParser xmlparser;
	
	
	public AttachSimulator(XMLParser xmlparser, SctpClient sctpClient)
	{
		this.xmlparser = xmlparser;
		this.sctpClient = sctpClient;
	}

	/**
	 * Getters
	 */
	public InetAddress getTransportLayerAddress()
	{
		return transportLayerAddress;
	}

	public InetAddress getPDNIpv4()
	{
		return PDNIpv4;
	}

	public String getTEID()
	{
		return TEID;
	}

	/**
	 * The Attach Sequence is initiated in this function..
	 * 
	 * @param xmlparser
	 */
	public boolean initiateAttachSequence(XMLParser xmlparser, String ueparams, String eNBUES1APID)
	{
		logger.info("Initiating Attach Sequence");

		S1APPacket reply1 = sendAttachRequest(ueparams, eNBUES1APID);
		if(reply1.getProcCode().equals("downlinkNASTransport"))
		{
			S1APPacket reply2 = sendAuthenticationResponse(reply1, eNBUES1APID);
			if(reply2!=null && reply2.getProcCode().equals("downlinkNASTransport"))
			{
				S1APPacket reply3 = sendSecurityModeComplete(reply2);
				if(reply3.getProcCode().equals("downlinkNASTransport"))
				{
					S1APPacket reply4 = sendESMInformationResponse(reply3);
					if(reply4.getProcCode().equals("InitialContextSetup"))
					{
						sendInitialContextSetupResponse(reply4);
						sendAttachComplete(reply4);
						return true;
					}
					else System.out.println("Attach(4) failure");
				}
				else System.out.println("Attach(3) failure");
			}
			else System.out.println("Attach(2) failure");
		}
		else
		{
			System.out.println("Attach(1) failure");
		}
		return false;
	}

	/**
	 * The first packet of the attach sequence, the Attach Request is sent to
	 * the MME in this function..
	 * 
	 * @param xmlparser
	 */
	//0911325476982143
	//String AttachArguments = "08" + ueparams.split(";")[0] + "05e0e000000000050202d011d1";
	public S1APPacket sendAttachRequest(String ueparams, String eNBUES1APID)
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

		S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "initialUEMessage", "ignore", values, true);

		return recievedPacket;
	}

	/**
	 * The second packet of the attach sequence, the Authentication Response is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public S1APPacket sendAuthenticationResponse(S1APPacket authenticationRequest, 
			String eNBUES1APID)
	{

		AttachSeqDemo obj = new AttachSeqDemo();
		// NAS PDU GENERATION
		String k = "465B5CE8B199B49FAA5F0A2EE238A6BC"; // key
		String op = "1918b840195c97017228127009ca194e"; // op values

		String NASPDUInAuthentication = authenticationRequest.getValue("NASPDU");

		String NASPDUInAuthenticationRequest = NASPDUInAuthentication.substring(2);
		String r = obj.ParseAuthRequest(NASPDUInAuthenticationRequest); // Parse
																		// Authentication
																		// Request
																		// Message
																		// and
																		// obtain
																		// Rand
																		// value

		if(r == null)
			return null;
		
		//
		//System.out.println("R Value:"+r);
		//
		// get the NAS response from the NAS classes!!
		String NASPDU = obj.SendAuthResp(r, k, op);
		// NASPDU=(NASPDU.length()/2) + NASPDU ;
		// System.out.println(NASPDU);
		//////////////////////////////////

		ArrayList <Value> values = new ArrayList <Value>();
		values.add(new Value("MMEUES1APID", "reject", authenticationRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", eNBUES1APID));
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);

		return recievedPacket;

	}

	/**
	 * The third packet of the attach sequence, the SecurityModeComplete packet
	 * is sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public S1APPacket sendSecurityModeComplete(S1APPacket securityModeCommand)
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

		S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);

		return recievedPacket;
	}

	/**
	 * The fourth packet of the attach sequence, the ESMInformationResponse is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public S1APPacket sendESMInformationResponse(S1APPacket esmInformationRequest)
	{
		// NAS PDU GENERATION
		String NASPDUInESMInformationRequest = esmInformationRequest.getValue("NASPDU");

		// get the NAS response from the NAS classes!!
		String NASPDU = "1d270f6cfb77010202da28120561706e2d310769786961636f6d03636f6d";
		//////////////////////////////////

		ArrayList <Value> values = new ArrayList <Value>();
		values.add(new Value("MMEUES1APID", "reject", esmInformationRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", esmInformationRequest.getValue("eNBUES1APID"))); // TODO
																									   // change
																									   // it
																									   // to
																									   // Dynamic!!!
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		S1APPacket recievedPacket = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);
		extractGTPData(recievedPacket);

		return recievedPacket;
	}

	/**
	 * The fifth packet of the attach sequence, the InitialContextSetupResponse
	 * is sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendInitialContextSetupResponse(S1APPacket initialContextSetupRequest)
	{

		ArrayList <Value> values = new ArrayList <Value>();
		values.add(new Value("MMEUES1APID", "reject", initialContextSetupRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", initialContextSetupRequest.getValue("eNBUES1APID")));
		values.add(new Value("ERABSetupListCtxtSURes", "ignore", "000032400a0a1fac11012800000021")); // TODO:
																									 // make
																									 // dynamic!!

		sendS1APacket("SuccessfulOutcome", "InitialContextSetup", "reject", values, false);
	}

	/**
	 * The sixth packet of the attach sequence, the AttachComplete packet is
	 * sent to the MME in this function..
	 * 
	 * @param xmlparser
	 */
	public void sendAttachComplete(S1APPacket initialContextSetupRequest)
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
	public S1APPacket sendS1APacket(String type, String procCode, String criticality, ArrayList <Value> values,
			Boolean recieve)
	{

		S1APPacket pac = new S1APPacket(type, procCode, criticality, values.size());

		for(int i = 0; i < values.size(); i++)
		{
			pac.addValue(values.get(i).typeOfValue, values.get(i).criticality, values.get(i).value.length() / 2,
					values.get(i).value);
		}

		pac.createPacket();
		byte [] message = pac.getBytePacket();

		logger.info("Sending Packet -- " + pac.toString());

		sctpClient.sendProtocolPayload(message, 18);

		if(recieve == true)
		{
			String reply = sctpClient.recieveSCTPMessage();

			S1APPacket recievedPacket = new S1APPacket();
			recievedPacket.parsePacket(reply);

			logger.info("Received Packet -- " + recievedPacket.toString());

			return recievedPacket;
		}
		return null;
	}

	public void extractGTPData(S1APPacket attachComplete)
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

		logger.info("Data Extracted From ESM InformationResponse - TransportLayerAddress:" + transportLayerAddress
				+ " PDNIPv4:" + PDNIpv4 + " TEID:" + TEID);
	}
}
