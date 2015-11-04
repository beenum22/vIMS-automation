package com.xflowresearch.nfv.testertool.enodeb;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;

import javax.xml.bind.DatatypeConverter;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.ue.nas.AttachSeqDemo;

/**
 * AttachSimulator class to establish s1 signaling with
 * MME and initiating the attach sequence for a UE with
 * the MME..
 * 
 * @author Ahmad Arslan
 *
 */
public class AttachSimulator {

	InetAddress transportLayerAddress;
	InetAddress PDNIpv4;
	String TEID;


	private class Value{
		public String typeOfValue;
		public String criticality;
		public String value;

		public Value(String typeOfValue, String criticality, String value) {
			super();
			this.typeOfValue = typeOfValue;
			this.criticality = criticality;
			this.value = value;
		}
	}

	private SctpClient sctpClient;

	public AttachSimulator(XMLParser xmlparser){
		sctpClient = new SctpClient();
		sctpClient.connectToHost(xmlparser.getMMEIP(), Integer.parseInt(xmlparser.getMMEPort()));
	}


	/**
	 * Getters
	 */
	public InetAddress getTransportLayerAddress() {
		return transportLayerAddress;
	}
	public InetAddress getPDNIpv4() {
		return PDNIpv4;
	}
	public String getTEID() {
		return TEID;
	}



	/**
	 * Establish S1Signalling with MME..
	 * @param xmlparser
	 */
	public Boolean establishS1Signalling(XMLParser xmlparser)
	{		
		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("GlobalENBID", "reject", xmlparser.getS1signallingParams().GlobalENBID));
		values.add(new Value("eNBname", "ignore", xmlparser.getS1signallingParams().eNBname));
		values.add(new Value("SupportedTAs", "reject", xmlparser.getS1signallingParams().SupportedTAs));
		values.add(new Value("DefaultPagingDRX", "ignore", xmlparser.getS1signallingParams().DefaultPagingDRX));

		String reply =  sendS1APacket("InitiatingMessage", "S1Setup", "reject", values, true);

		S1APPacket recievedPacket = new S1APPacket();
		recievedPacket.parsePacket(reply);

		if(recievedPacket.getType().equals("SuccessfulOutcome"))
		{
			return true;
		}
		else
			return false;
	}


	/**
	 * The Attach Sequence is initiated in this
	 * function..
	 * @param xmlparser
	 */
	public void initiateAttachSequence(XMLParser xmlparser)
	{
		S1APPacket reply1 = sendAttachRequest(xmlparser);
		if(reply1.getProcCode().equals("downlinkNASTransport") )
		{
			S1APPacket reply2 = sendAuthenticationResponse(xmlparser, reply1);
			if(reply2.getProcCode().equals("downlinkNASTransport"))
			{
				S1APPacket reply3 = sendSecurityModeComplete(xmlparser, reply2);
				if(reply3.getProcCode().equals("downlinkNASTransport"))
				{
					S1APPacket reply4 = sendESMInformationResponse(xmlparser, reply3);
					if(reply4.getProcCode().equals("InitialContextSetup"))
					{
						sendInitialContextSetupResponse(xmlparser, reply4);
						sendAttachComplete(xmlparser, reply4);
					}
					else
						System.out.println("Attach(4) failure");
				}
				else
					System.out.println("Attach(3) failure");
			}
			else
				System.out.println("Attach(2) failure");
		}
		else{
			System.out.println("Attach(1) failure");
		}
	}



	/**
	 * The first packet of the attach sequence, the Attach
	 * Request is sent to the MME in this function..
	 * @param xmlparser
	 */
	public S1APPacket sendAttachRequest(XMLParser xmlparser)
	{
		//////NAS packet Generation////////////////////////////
		String AttachArguments ="08091132547698214305e0e000000000050202d011d1";
		AttachSeqDemo obj = new AttachSeqDemo();
		String NASPDU = obj.SendAttachPack(AttachArguments);
		//////////////////////////////////

		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("eNBUES1APID", "reject", xmlparser.geteNBUES1APID()));
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("TAI", "reject", xmlparser.getTAI()));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getEUTRANCGI()));
		values.add(new Value("RRCEstablishmentCause", "ignore", xmlparser.getRRCEstablishmentCause()));

		String reply = sendS1APacket("InitiatingMessage", "initialUEMessage", "ignore", values, true);

		S1APPacket recievedPacket = new S1APPacket();
		recievedPacket.parsePacket(reply);
		return recievedPacket;
	}

	/**
	 * The second packet of the attach sequence, the
	 * Authentication Response is sent to the MME in this function..
	 * @param xmlparser
	 */
	public S1APPacket sendAuthenticationResponse(XMLParser xmlparser, S1APPacket authenticationRequest){

		
		AttachSeqDemo obj =new AttachSeqDemo();
		//NAS PDU GENERATION
		String k= "465B5CE8B199B49FAA5F0A2EE238A6BC"; //key
		String op= "1918b840195c97017228127009ca194e"; //op values
		
		
		String NASPDUInAuthentication= authenticationRequest.getValue("NASPDU");
		//String NASPDUInAuthentication = "07520067c6697351ff4aec29cdbaabf2fbe3461008199eed4aa3b9b93ba100c2e82de53c";
		
		
		String NASPDUInAuthenticationRequest=NASPDUInAuthentication.substring(2);
		//System.out.println(NASPDUInAuthenticationRequest);
		String r= obj.ParseAuthRequest(NASPDUInAuthenticationRequest); //Parse Authentication Request Message and obtain Rand value
		
		//System.out.println (r);
		
		//get the NAS response from the NAS classes!!
		String NASPDU = obj.SendAuthResp ( r, k, op );
		//NASPDU=(NASPDU.length()/2) + NASPDU ;
		//System.out.println(NASPDU);
		//////////////////////////////////

		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("MMEUES1APID", "reject", authenticationRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", "0001"));                               //TODO change it to Dynamic!!!
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		String reply = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);

		S1APPacket recievedPacket = new S1APPacket();
		recievedPacket.parsePacket(reply);
		return recievedPacket;
		
	}



	/**
	 * The third packet of the attach sequence, the
	 * SecurityModeComplete packet is sent to the MME 
	 * in this function..
	 * @param xmlparser
	 */
	public S1APPacket sendSecurityModeComplete(XMLParser xmlparser, S1APPacket securityModeCommand){

		//NAS PDU GENERATION
		String NASPDUInSecurityModeCommand = securityModeCommand.getValue("NASPDU");

		//get the NAS response from the NAS classes!!
		String NASPDU = "08471136cdbe00075e";
		//////////////////////////////////

		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("MMEUES1APID", "reject", securityModeCommand.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", securityModeCommand.getValue("eNBUES1APID")));                               //TODO change it to Dynamic!!!
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		String reply = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);

		S1APPacket recievedPacket = new S1APPacket();
		recievedPacket.parsePacket(reply);
		return recievedPacket;
	}


	/**
	 * The fourth packet of the attach sequence, the
	 * ESMInformationResponse is sent to the MME in 
	 * this function..
	 * @param xmlparser
	 */
	public S1APPacket sendESMInformationResponse(XMLParser xmlparser, S1APPacket esmInformationRequest){
		//NAS PDU GENERATION
		String NASPDUInESMInformationRequest = esmInformationRequest.getValue("NASPDU");

		//get the NAS response from the NAS classes!!
		String NASPDU = "1d270f6cfb77010202da28120561706e2d310769786961636f6d03636f6d";
		//////////////////////////////////

		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("MMEUES1APID", "reject", esmInformationRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", esmInformationRequest.getValue("eNBUES1APID")));                               //TODO change it to Dynamic!!!
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		String reply = sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, true);

		S1APPacket recievedPacket = new S1APPacket();
		recievedPacket.parsePacket(reply);
		extractGTPData(recievedPacket);
		return recievedPacket;
	}


	/**
	 * The fifth packet of the attach sequence, the
	 * InitialContextSetupResponse is sent to the MME
	 * in this function..
	 * @param xmlparser
	 */
	public void sendInitialContextSetupResponse(XMLParser xmlparser, S1APPacket initialContextSetupRequest){

		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("MMEUES1APID", "reject", initialContextSetupRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", initialContextSetupRequest.getValue("eNBUES1APID")));
		values.add(new Value("ERABSetupListCtxtSURes", "ignore", "000032400a0a1fac11012800000021"));  //TODO: make dynamic!!

		sendS1APacket("SuccessfulOutcome", "InitialContextSetup", "reject", values, false);
	}


	/**
	 * The sixth packet of the attach sequence, the
	 * AttachComplete packet is sent to the MME in 
	 * this function..
	 * @param xmlparser
	 */
	public void sendAttachComplete(XMLParser xmlparser, S1APPacket initialContextSetupRequest){
		//NAS PDU GENERATION
		//String NASPDUInInitialContextSetupRequest = initialContextSetupRequest.getValue("NASPDU");

		//get the NAS response from the NAS classes!!
		String NASPDU = "0d27cd3c638302074300035200c2";
		//////////////////////////////////


		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("MMEUES1APID", "reject", initialContextSetupRequest.getValue("MMEUES1APID")));
		values.add(new Value("eNBUES1APID", "reject", initialContextSetupRequest.getValue("eNBUES1APID")));
		values.add(new Value("NASPDU", "reject", NASPDU));
		values.add(new Value("EUTRANCGI", "ignore", xmlparser.getAuthenticationResponseParams().EUTRANCGI));
		values.add(new Value("TAI", "ignore", xmlparser.getAuthenticationResponseParams().TAI));

		sendS1APacket("InitiatingMessage", "uplinkNASTransport", "ignore", values, false);
	}


	/**
	 * Function to generate and send any sort of s1AP Packet, 
	 * packet controlled by the input parameters.. The return
	 * is the hex-encoded reply received from the MME..
	 * @param type
	 * @param procCode
	 * @param criticality
	 * @param values
	 * @return reply
	 */
	public String sendS1APacket(String type, String procCode, 
			String criticality, ArrayList<Value> values, Boolean recieve){

		S1APPacket pac = new S1APPacket(type, procCode, criticality, values.size());

		for(int i=0;i<values.size();i++)
		{
			pac.addValue(values.get(i).typeOfValue, values.get(i).criticality, 
					values.get(i).value.length()/2, values.get(i).value);
		}

		pac.createPacket();
		byte [] message = pac.getBytePacket();

		sctpClient.sendProtocolPayload(message, 18);

		if(recieve == true)
		{
			String reply =  sctpClient.recieveSCTPMessage();
			return reply;
		}
		return null;
	}




	public void extractGTPData(S1APPacket attachComplete)
	{
		String value =  attachComplete.getValue("ERABToBeSetupListCtxtSUReq");
		value = value.substring(24, value.length());

		String ip1 = value.substring(0, 8);
		TEID = value.substring(8, 16);
		String ip2 = value.substring(146, 154);

		try {
			transportLayerAddress = InetAddress.getByAddress(DatatypeConverter.parseHexBinary(ip1));
			PDNIpv4 = InetAddress.getByAddress(DatatypeConverter.parseHexBinary(ip2));
		} catch (UnknownHostException e) 
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		System.out.println(transportLayerAddress.toString());
		System.out.println(PDNIpv4.toString());


		System.out.println(TEID);

//		/System.out.println(value);

	}
}
