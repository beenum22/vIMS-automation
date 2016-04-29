package com.xflowresearch.nfv.testertool.enodeb.s1u;

import java.net.InetAddress;

public class User
{
	private String TEID;
	private String IP;
	private Integer ports[];
	private String eNBUES1APID;
	private InetAddress transportLayerAddress;
	
	public void setTransportLayerAddress(InetAddress tla)
	{
		this.transportLayerAddress = tla;
	}
	
	public InetAddress getTransportLayerAddress()
	{
		return transportLayerAddress;
	}
	
	public String geteNBUES1APID()
	{
		return eNBUES1APID;
	}

	public void seteNBUES1APID(String eNBUES1APID)
	{
		this.eNBUES1APID = eNBUES1APID;
	}

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
