package com.xflowresearch.nfv.testertool.enodeb.s1u;

public class User
{
	private String TEID;
	private String IP;
	private Integer ports[];

	public String getTEID()
	{
		return TEID;
	}

	public void setTEID(String tEID)
	{
		TEID = tEID;
	}

	public String getIP()
	{
		return IP;
	}

	public void setIP(String iP)
	{
		IP = iP;
	}

	public Integer [] getPorts()
	{
		return ports;
	}

	public void setPorts(Integer [] ports)
	{
		this.ports = ports;
	}
}
