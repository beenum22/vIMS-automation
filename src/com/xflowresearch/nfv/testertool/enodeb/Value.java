package com.xflowresearch.nfv.testertool.enodeb;

public class Value
{
	public String typeOfValue;
	public String criticality;
	public String value;

	public Value(String typeOfValue, String criticality, String value)
	{
		super();
		this.typeOfValue = typeOfValue;
		this.criticality = criticality;
		this.value = value;
	}
}