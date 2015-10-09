package com.xflowresearch.nfv.testertool.enodeb;

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

	
	public void s1apTestPacket()
	{
		/** Test S1AP Packet Creation Here!! **/
		
		//////NAS packet Generation////////////////////////////
		String AttachArguments ="08091132547698214305e0e000000000050202d011d1";
		String Reply = "07520067c6697351ff4aec29cdbaabf2fbe3461008199eed4aa3b9b93ba100c2e82de53c";
		
		AttachSeqDemo obj =new AttachSeqDemo();
		String NASPDU = obj.SendAttachPack(AttachArguments);
		System.out.println("Attach Request:" + " " +obj.SendAttachPack(AttachArguments));
		//////////////////////////////////

		sctpClient.connectToHost("127.0.0.1", 1111);
		
		S1APPacket pac = new S1APPacket("InitiatingMessage", "initialUEMessage", "ignore", 5);
		
		pac.addValue("eNBUES1APID", "reject", 2, "0001");
//		pac.addValue("NASPDU", "reject", 25, "1907417108091132547698214305e0e000000000050202d011d1");
		pac.addValue("NASPDU", "reject", (NASPDU.length()/2), NASPDU);
		pac.addValue("TAI", "reject", 6, "0010f1321011");
		pac.addValue("EUTRANCGI", "ignore", 18, "4010f13201388010000000010004ac110128");
		pac.addValue("RRCEstablishmentCause", "ignore", 1, "30");
		
		pac.createPacket();
		
		byte [] message = pac.getBytePacket();

		sctpClient.sendProtocolPayload(message, 18);
		try {
			Thread.sleep(3000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		sctpClient.disconnectFromHost();
		/** Test S1AP Packet Creation Here!! **/
	}
}
