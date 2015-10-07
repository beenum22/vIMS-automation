package com.xflowresearch.nfv.testertool.ue.nas;

public class AttachSeqDemo {
	
	
	public String SendAttachPack( String AttachArguments){
		
		NASImplementation NASobject =new NASImplementation();
		return (NASobject.NASAttachRequest(AttachArguments));
		
		
	}
	
	
	public String ParseAttachRespMsg(String Reply){
		
		String [] Array;
		NASImplementation NASobject =new NASImplementation();
		Array= NASobject.AttachRepParser(Reply);
		String AuthResp="SecurityHeaderType: " + Array[0] + ", "+ "ProtocolDiscriminator: " + Array[1]
				+ "," + "EPSMobilityManagementMsg: " + Array[2] +  "," 
				+ "AuthParameterRandValue:" + Array[3];
		
		return AuthResp;
	}
	
	
	public static void main(String args[]){
		
		String AttachArguments ="08091132547698214305e0e000000000050202d011d1";
		String Reply = "07520067c6697351ff4aec29cdbaabf2fbe3461008199eed4aa3b9b93ba100c2e82de53c";
		
		AttachSeqDemo obj =new AttachSeqDemo();
		
		System.out.println("Attach Request:" + " " +obj.SendAttachPack(AttachArguments));
		System.out.println("Authentication Req Message :" + "\n " + obj.ParseAttachRespMsg(Reply));
		
		
	}

}
