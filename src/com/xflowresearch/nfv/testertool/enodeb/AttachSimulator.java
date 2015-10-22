package com.xflowresearch.nfv.testertool.enodeb;

import com.xflowresearch.nfv.testertool.common.XMLParser;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;
import com.xflowresearch.nfv.testertool.ue.nas.AttachSeqDemo;

public class AttachSimulator {
	
	private SctpClient sctpClient;
	
	public AttachSimulator(){
		sctpClient = new SctpClient();
		
	}
	

	public void establishS1Signalling(){
		
	}
	public void initiateAttachSequence(){
		
	}

	public void sendS1SetupMessage(XMLParser xmlparser){
		String pac = xmlparser.getPLMN();
		
		sctpClient.connectToHost(xmlparser.getMMEIP(), Integer.parseInt(xmlparser.getMMEPort()));
		byte [] message = hexStringToByteArray(pac);

		sctpClient.sendProtocolPayload(message, 18);
		sctpClient.recieveSCTPMessage();
		/** Test S1AP Packet Creation Here!! **/
	}
	
	public void s1apTestPacket(XMLParser xmlparser)
	{
		/** Test S1AP Packet Creation Here!! **/
		
		//////NAS packet Generation////////////////////////////
		String AttachArguments ="08091132547698214305e0e000000000050202d011d1";
		
		AttachSeqDemo obj = new AttachSeqDemo();
		String NASPDU = obj.SendAttachPack(AttachArguments);
		//////////////////////////////////

		
		S1APPacket pac = new S1APPacket("InitiatingMessage", "initialUEMessage", "ignore", 5);
		
		pac.addValue("eNBUES1APID", "reject", 2, xmlparser.geteNBUES1APID());
		pac.addValue("NASPDU", "reject", (NASPDU.length()/2), NASPDU);
		pac.addValue("TAI", "reject", 6, xmlparser.getTAI());
		pac.addValue("EUTRANCGI", "ignore", 18, xmlparser.getEUTRANCGI());
		pac.addValue("RRCEstablishmentCause", "ignore", 1, xmlparser.getRRCEstablishmentCause());
		
		pac.createPacket();
		byte [] message = pac.getBytePacket();

		sctpClient.sendProtocolPayload(message, 18);
		sctpClient.recieveSCTPMessage();
		//sctpClient.disconnectFromHost();
		/** Test S1AP Packet Creation Here!! **/
		
		
		
		//second packet
		String secondPacket = "000d403800000500000005c021f600d8000800020001001a000c0b075308634f82417968ca98006440080010f13201388010004340060010f1321011";
		byte [] message1 = hexStringToByteArray(secondPacket);
		sctpClient.sendProtocolPayload(message, 18);
		sctpClient.recieveSCTPMessage();
	}
	

	public static byte[] hexStringToByteArray(String s)
	{
		byte[] b = new byte[s.length() / 2];
		for (int i = 0; i < b.length; i++)
		{
			int index = i * 2;
			int v = Integer.parseInt(s.substring(index, index + 2), 16);
			b[i] = (byte) v;
		}
		return b;
	}
}
