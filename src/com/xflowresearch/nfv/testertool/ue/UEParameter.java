package com.xflowresearch.nfv.testertool.ue;

public class UEParameter
{
	String IMSI, K;
	
	public UEParameter(String IMSI, String K)
	{
		this.IMSI = IMSI;
		this.K = K;
	}
	
	public String toString()
	{
		return IMSI + ";" + K;
	}
}
