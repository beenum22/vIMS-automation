package com.xflowresearch.nfv.testertool.enodeb;

import java.util.ArrayList;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.ue.nas.AttachSeqDemo;

public class AttachSimulator {

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

	
	
	public void establishS1Signalling(XMLParser xmlparser)
	{		
		ArrayList<Value> values = new ArrayList<Value>();
		values.add(new Value("GlobalENBID", "reject", xmlparser.getS1signallingParams().GlobalENBID));
		values.add(new Value("eNBname", "ignore", xmlparser.getS1signallingParams().eNBname));
		values.add(new Value("SupportedTAs", "reject", xmlparser.getS1signallingParams().SupportedTAs));
		values.add(new Value("DefaultPagingDRX", "ignore", xmlparser.getS1signallingParams().DefaultPagingDRX));
		
		sendS1APacket("InitiatingMessage", "S1Setup", "reject", values);
	}
	
	public void initiateAttachSequence(){

	}

	public void sendInitialUEMessage(XMLParser xmlparser)
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
		
		sendS1APacket("InitiatingMessage", "initialUEMessage", "ignore", values);
	}


	public void sendS1APacket(String type, String procCode, 
			String criticality, ArrayList<Value> values)
	{
		S1APPacket pac = new S1APPacket(type, procCode, criticality, values.size());

		for(int i=0;i<values.size();i++)
		{
			pac.addValue(values.get(i).typeOfValue, values.get(i).criticality, 
					values.get(i).value.length()/2, values.get(i).value);
		}

		pac.createPacket();
		byte [] message = pac.getBytePacket();

		sctpClient.sendProtocolPayload(message, 18);
		sctpClient.recieveSCTPMessage();
	}
	
}
