package com.xflowresearch.nfv.testertool.ue;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.ArrayList;
import java.util.Map;
import java.util.TreeMap;

import org.pcap4j.packet.IpV4Packet;

import com.xflowresearch.nfv.testertool.common.ConfigHandler;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;

class GTPResponseListener implements Runnable
{
	private DatagramSocket socket;
	private UEController ueController;
	
	public GTPResponseListener(UEController ueController)
	{
		this.ueController = ueController;
	}
	
	public void run()
	{
		try
		{
			socket = new DatagramSocket(2152);
			
			while(true)
			{
				byte [] receiveData = new byte[1024];
				DatagramPacket p = new DatagramPacket(receiveData, receiveData.length);
				
				socket.receive(p);
				new Thread(new Processor(p)).start();
			}
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	class Processor implements Runnable
	{
		DatagramPacket p;
		
		public Processor(DatagramPacket p)
		{
			this.p = p;
		}
		
		public void run()
		{
			try
			{
				byte [] data = p.getData();
				IpV4Packet recvdPacket = IpV4Packet.newPacket(data, 8, data.length-8);			
				ueController.processPacket(recvdPacket);
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}
}

public class UEController
{	
	boolean debugOnScreen = true;

	private TreeMap<String, UE> UEs;

	private Object uEListLock;
	//private Object socketLock;

	//private XMLParser xmlparser;
	private ArrayList<eNodeB> eNodeBs;
	
	//private PrintWriter attachLogWriter;

	public void startGtpListener()
	{
		new Thread(new GTPResponseListener(this)).start();
	}
	
	public void processPacket(IpV4Packet p)
	{
		try
		{
			String addr = p.getHeader().getDstAddr().getHostAddress();
			System.out.println("Received: " + addr);
			UE temp = null;
			
			//UEs.entrySet();
			
			synchronized(uEListLock)
			{
				for(Map.Entry<String, UE> entry : UEs.entrySet())
				{
					//System.out.println(entry.getValue().getPdnipv4());
					//System.out.println("comparing " + entry.getValue().getPdnipv4() + " " + addr);
					
					if(entry.getValue().getPdnipv4().equals(addr))
					{
						temp = entry.getValue();
						break;
					}
				}
			}
			
			temp.processPacket(p);
		}
		
		catch(NullPointerException npe)
		{
			System.out.println(npe);
		}
	}
	
	public UEController(ConfigHandler xmlparser, ArrayList<eNodeB> eNodeBs)
	{
		try
		{
			UEs = new TreeMap<>();
	
			uEListLock = new Object();
			//socketLock = new Object();
			
			this.eNodeBs = eNodeBs;
	
			//this.xmlparser = xmlparser;
		
			//attachLogWriter = new PrintWriter(new File("attach_log.txt"));
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	public void addUE(UE ue)
	{
		synchronized (uEListLock)
		{
			UEs.put(ue.geteNBUES1APID(), ue);
		}
	}
	
	public void sendAttachRequest(UE ue)
	{
		addUE(ue);

		try
		{
			eNodeBs.get(0).getUserControlInterface().sendAttachRequest("Attach;" + ue.geteNBUES1APID() + ";" + ue.UEParameters.toString());
		}

		catch (Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	class ResponseProcessor implements Runnable
	{
		String response;

		public ResponseProcessor(String response)
		{
			this.response = response;
		}

		@Override
		public void run()
		{
			UE temp = null;

			try
			{
				if(!response.split(";")[1].equals("attachfailure"))
				{
					//attachLogWriter.write("Successfuly attached: " + response.split(";")[0] + "<br>");
					//attachLogWriter.flush();
					
					synchronized (uEListLock)
					{
						temp = UEs.get((response.split(";")[0]));
					}
	
					if(temp != null)
					{
						temp.setStatus(true);
						temp.setId(response.split(";")[0]);
						temp.setPdinpv4(eNodeBs.get(0).getUser(response.split(";")[0]).getIP());
						
						synchronized(temp.getLock())
						{
							temp.getLock().notify();
						}
						
						//Thread.sleep(1000);
						//temp.simulateHttpRequest(eNodeBs.get(0).getUser(response.split(";")[0]));
					}
	
					else
					{
						System.out.println("UE not found");
					}
				}
	
				else
				{
					System.out.println(response.split(";")[0] + " failed");
				}
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}

	public String doHttp(String id)
	{
		try
		{
			UE temp = UEs.get(id);
			
			new Thread(new Runnable()
			{
				public void run()
				{
					temp.simulateHttpRequest(eNodeBs.get(0).getUser(id));
				}
			}).start();

			System.out.println("waiting...");
			synchronized(temp.getLock())
			{
				temp.getLock().wait();
			}
			System.out.println("resumed...");
			
			return temp.getResponse();
		}

		catch(Exception exc)
		{
			exc.printStackTrace();
			return "failed";
		}
	}

	public void processAttachResponse(String response)
	{
		new Thread(new ResponseProcessor(response)).start();
	}
}