package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.io.UnsupportedEncodingException;
import java.math.BigInteger;

public class GTPacket {
	
	private String header;
	
	//Flags fields:
	private String version;
	private int protocolType;
	private int reserved;
	private int nextExtensionHeaderPresent;
	private int isSeqNoPresent;
	private int isNPDUNumberPresent;
	
	
	private String messageType;
	private String length;
	private String TEID;
	
	
	private String TPDU;


	/**
	 * @param version
	 * @param pritocolType
	 * @param reserved
	 * @param nextExtensionHeaderPresent
	 * @param isSeqNoPresent
	 * @param isNPDUNumberPresent
	 */
	public GTPacket(String version, int protocolType, int reserved, int nextExtensionHeaderPresent, int isSeqNoPresent,
			int isNPDUNumberPresent) {
		super();
		this.version = version;
		this.protocolType = protocolType;
		this.reserved = reserved;
		this.nextExtensionHeaderPresent = nextExtensionHeaderPresent;
		this.isSeqNoPresent = isSeqNoPresent;
		this.isNPDUNumberPresent = isNPDUNumberPresent;
		
		String temp = version + protocolType + reserved + nextExtensionHeaderPresent + isSeqNoPresent + isNPDUNumberPresent;
		
		try {
			header = String.format("%010x", new BigInteger(1, temp.getBytes("UTF-8")));
			header = header.substring(header.length()-2, header.length());
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
	}


	public void setMessageType(String messageType) {
		this.messageType = messageType;
	}
	
	/**
	 * number of bytes as integer 
	 * @param length
	 */
	public void setLength(int length) {
		String len = Integer.toHexString(length);
		if(len.length() == 3)
			len = "0" + len;
		if(len.length() == 2)
			len = "00" + len;
		if(len.length() == 1)
			len = "000" + len;
		this.length = len;
	}
	
	public void setTEID(String tEID) {
		TEID = tEID;
	}
	
	public void setTPDU(String TPDU){
		this.TPDU = TPDU;
	}
	
	public byte[] getPacket(){
		String pac = header + messageType + length + TEID + TPDU;
		return hexStringToByteArray(pac); 
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
