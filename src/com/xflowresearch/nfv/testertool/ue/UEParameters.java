package com.xflowresearch.nfv.testertool.ue;

public class UEParameters
{
	String IMSI, K;
	
	public UEParameters(String IMSI, String K)
	{
		this.IMSI = IMSI;
		this.K = K;
	}
	
	public String toString()
	{
		return IMSI + ";" + K;
	}
}
