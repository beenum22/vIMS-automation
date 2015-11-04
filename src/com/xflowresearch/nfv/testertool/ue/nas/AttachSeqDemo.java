package com.xflowresearch.nfv.testertool.ue.nas;

import javax.xml.bind.DatatypeConverter;

import com.xflowresearch.nfv.testertool.ue.nas.Algo;


public class AttachSeqDemo {
	
	
	public String SendAttachPack( String AttachArguments){
		
		NASImplementation NASobject =new NASImplementation();
		String NASPDU = NASobject.NASAttachRequest(AttachArguments);
		NASPDU = Integer.toHexString(NASPDU.length()/2) + NASPDU;
		return NASPDU;	
	}
	
	
	public String ParseAttachRespMsg(String Reply){
		
		String [] Array;
		NASImplementation NASobject =new NASImplementation();
		Array= NASobject.respParser(Reply);
		String AuthReq="SecurityHeaderType: " + Array[0] + ", "+ "ProtocolDiscriminator: " + Array[1]
				+ "," + "EPSMobilityManagementMsg: " + Array[2] +  "," 
				+ "AuthParameterRandValue:" + Array[3];
		
		return AuthReq;
	}
	
	public String ParseAuthRequest(String AuthReqString)
	{
		String [] Array;
		NASImplementation NASobject =new NASImplementation();
		Array= NASobject.respParser(AuthReqString);
		String AuthResponse="SecurityHeaderType: " + Array[0] + ", "+ "ProtocolDiscriminator: " + Array[1]
				+ "," + "EPSMobilityManagementMsg: " + Array[2] +  "," 
				+ "AuthParameterRandValue:" + Array[3];
		String RAND= Array[3];
		System.out.println (AuthResponse);
		return RAND;
		
	}
	
	public String SendAuthResp (String r,String k,String op ){
		
		byte []ck = new byte [16];
		byte []ik= new byte [16];
		byte []ak= new byte[6];
		byte [] res = new byte [8];
		

		byte[] key = DatatypeConverter.parseHexBinary(k);
		byte [] rand =DatatypeConverter.parseHexBinary(r);
		byte[] OP=DatatypeConverter.parseHexBinary(op);

		Algo obj =new Algo(key,OP);
		obj.f2345(rand, res, ck, ik, ak);
		String RES=DatatypeConverter.printHexBinary(res);
		
		
		NASImplementation NASobject =new NASImplementation();
		
		
		String length =Integer.toString(r.length()/2);
		
		String AuthResponse= NASobject.NASAuthenticationResponse(RES,length);
		//AuthResponse = Integer.toHexString(AuthResponse.length()/2) + AuthResponse;
		return AuthResponse;
		
	}
	
	public static void main(String args[]){
		
		String k= "465B5CE8B199B49FAA5F0A2EE238A6BC"; //key
		String r="67c6697351ff4aec29cdbaabf2fbe346"; //rand
		String op= "1918b840195c97017228127009ca194e";
		
		
		String AttachArguments ="08091132547698214305e0e000000000050202d011d1";
		String Reply = "075C0067c6697351ff4aec29cdbaabf2fbe3461008199eed4aa3b9b93ba100c2e82de53c";
		//String Reply ="075c14";
		AttachSeqDemo obj =new AttachSeqDemo();
		
		
		System.out.println(obj.SendAuthResp ( r, k, op ));

		
		
	}
	

}
