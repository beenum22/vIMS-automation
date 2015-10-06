package com.xflowresearch.nfv.testertool.enodeb;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.xflowresearch.nfv.testertool.enodeb.s1mme.S1APPacket;
import com.xflowresearch.nfv.testertool.enodeb.s1mme.SctpClient;

/**
 * eNodeB
 * 
 *	eNodeB class that executes on the eNodeB thread
 *	and initiates the eNodeB functionality.
 *
 * 
 * @author ahmadarslan
 */
public class eNodeB implements Runnable
{
	private static eNodeB instance = new eNodeB();

	private static final Logger logger = LoggerFactory.getLogger("eNodeBLogger");


	private eNodeB(){

	}


	public static eNodeB getInstance( ) {
		return instance;
	}


	public Logger getLogger(){
		return eNodeB.logger;
	}


	@Override
	public void run() {
		
		logger.info("eNodeB started");

		s1apTestPacket();
		
	}



	public void s1apTestPacket(){
		/** Test S1AP Packet Creation Here!! **/

		SctpClient client = new SctpClient();
		client.connectToHost("127.0.0.1", 1111);
		
		S1APPacket pac = new S1APPacket("InitiatingMessage", "initialUEMessage", "ignore", 5);
		pac.addValue("eNBUES1APID", "reject", 2, "0001");
		pac.addValue("NASPDU", "reject", 26, "1907417108091132547698214305e0e000000000050202d011d1");
		pac.addValue("TAI", "reject", 6, "0010f1321011");
		pac.addValue("EUTRANCGI", "ignore", 18, "4010f13201388010000000010004ac110128");
		pac.addValue("RRCEstablishmentCause", "ignore", 1, "30");
		
		pac.createPacket();
		
		byte [] message = pac.getBytePacket();

		client.sendProtocolPayload(message, 18);
		try {
			Thread.sleep(3000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		client.disconnectFromHost();
		/** Test S1AP Packet Creation Here!! **/
	}
}
