package com.xflowresearch.nfv.testertool.enodeb.s1mme;

import java.util.ArrayList;

/**
 * S1APPacket
 * 
 *	S1APPacket class that allows creation of
 *	an S1AP packet given the input parameters.
 * 
 * @author ahmadarslan
 */
public class S1APPacket
{

	private String header;
	private String value;

	private String type;
	private String procCode;
	private String criticality;
	private int lengthOfValues;
	private int numOfValues;

	public S1APPacket(){

	}
	public S1APPacket(String type, String procCode, String criticality, int numOfValues){
		header="";
		value="";

		this.type = type;
		this.procCode = procCode;
		this.criticality = criticality;
		this.numOfValues = numOfValues;
	}

	public class Value
	{
		String protocolIE;
		String criticality;
		int lengthOfValue;
		String value;

		public Value(){

		}
		public Value(String protocolIE, String criticality, int lengthOfValue, String value) {
			super();
			this.protocolIE = protocolIE;
			this.criticality = criticality;
			this.lengthOfValue = lengthOfValue;
			this.value = value;
		}	
	}
	private ArrayList<Value> values = new ArrayList<Value>();

	public void addValue(String protocolIE, String criticality, int lengthOfValue, String value){
		Value temp = new Value(protocolIE, criticality, lengthOfValue, value);
		values.add(temp);
	}


	public String getPacket(){
		return header+value;
	}

	public byte[] getBytePacket(){
		return hexStringToByteArray(header+value);
	}


	public String getType() {
		return type;
	}
	public ArrayList<Value> getValues() {
		return values;
	}
	public String getProcCode() {
		return procCode;
	}
	public String getCriticality() {
		return criticality;
	}
	public int getLengthOfValues(){
		return lengthOfValues;
	}
	public int getNumOfValues() {
		return numOfValues;
	}



	public void createPacket(){
		//header fields initialization
		insertPacketType();
		insertProcCode();
		insertCriticality();

		//values fields initialization
		insertNumOfValues();
		insertValues();

		insertByteValueLength();
	}

	/** Functions to create a packet **/
	public void insertPacketType(){
		String typeHexCode = S1APDefinitions.Type.fromString(type).getHexCode();
		header += typeHexCode;
	}

	public void insertProcCode(){
		String procCodeHexValue = S1APDefinitions.ProcedureCode.fromString(procCode).getHexCode();
		header += procCodeHexValue;
	}

	public void insertCriticality(){
		String criticalityHexCode = S1APDefinitions.Criticality.fromString(criticality).getHexCode();
		header += criticalityHexCode;
	}

	public void insertNumOfValues(){
		value += "00000" + Integer.toHexString(numOfValues);
	}

	public void insertByteValueLength(){
		String valueLength = Integer.toHexString((value.length()/2));

		if(valueLength.length() == 1)
			valueLength = "0" + valueLength;

		header += valueLength;
	}


	public void insertValues()
	{
		for(int i=0; i<numOfValues; i++)
		{
			S1APDefinitions.IEDict ie = S1APDefinitions.IEDict.fromString(values.get(i).protocolIE);
			String ieHexCode = ie.getHexCode();
			if(ieHexCode.length() == 1)
				ieHexCode = "000"+ ieHexCode;
			if(ieHexCode.length() == 2)
				ieHexCode = "00"+ ieHexCode;
			if(ieHexCode.length() == 3)
				ieHexCode = "0"+ ieHexCode;
			value += ieHexCode;  //protocol IE!!


			String criticayHexCode = S1APDefinitions.Criticality.fromString(values.get(i).criticality).getHexCode();
			value += criticayHexCode; //criticality


			String valLength = Integer.toHexString(values.get(i).lengthOfValue);
			if(valLength.length() == 1)
				valLength = "0"+valLength;
			value += valLength; //valuelength

			value += values.get(i).value;
		}
	}
	/** Functions to create a packet **/





	/** Functions to parse a packet **/
	public void parsePacket(String packet)
	{	
		header = packet.substring(0, 10);
		
		//parse fields from header..
		type = S1APDefinitions.Type.hexToType(header.substring(0, 2));
		procCode = S1APDefinitions.ProcedureCode.hexToProcedureCode(header.substring(2, 4));
		criticality = S1APDefinitions.Criticality.hexToCriticality(header.substring(4, 6));

		String lengthOfValuesHex = header.substring(6, 8);
		
		if(!lengthOfValuesHex.equals("80"))//if not 80 -- corner case!!
		{
			lengthOfValues = Integer.parseInt(header.substring(6, 8), 16);
			value = packet.substring(8, packet.length());
		}
		else
		{
			lengthOfValues = Integer.parseInt(header.substring(8, 10), 16);
			value = packet.substring(10, packet.length());
		}
		/*System.out.println("type:"+type);
		System.out.println("procCode:"+procCode);
		System.out.println("criticality:"+criticality);
		System.out.println("lengthOfValues:"+lengthOfValues);*/

		//parse fields from value..
		numOfValues = Integer.parseInt(value.substring(0, 6), 16);

		int a = 6, b = 10;

		//System.out.println("header:"+header);
		//System.out.println("value:"+value);

		for(int i=0;i<numOfValues;i++)
		{
			//System.out.println("\nItem_"+(i+1));
			Value temp = new Value();
			
			temp.protocolIE = S1APDefinitions.IEDict.hexToIEDict(value.substring(a, b).substring(2, 4));
			a = b; b += 2;
			
			temp.criticality = S1APDefinitions.Criticality.hexToCriticality(value.substring(a, b));
			a = b; b += 2;
			
			String lengthOfValueHex = value.substring(a, b); // length greater than 128... '80' corner case!!
			if(lengthOfValueHex.equals("80"))
			{
				a = b; b += 2; 
			}
			temp.lengthOfValue = Integer.parseInt(value.substring(a, b), 16);
			a = b; b += (2*temp.lengthOfValue);
			
			
			temp.value = value.substring(a, b);
			a = b; b += 4;

			//System.out.println("protocolIE:"+temp.protocolIE+"\ncriticality:"+temp.criticality+"\nlengthOfValue:"+temp.lengthOfValue+"\nvalue:"+temp.value);

			values.add(temp);	
		}
	}
	/** Functions to parse a packet **/




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
