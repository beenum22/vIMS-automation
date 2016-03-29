package com.xflowresearch.nfv.testertool.ue;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLConnection;
import java.net.UnknownHostException;

public class HTTPClient
{
	public void sendRequest(String srcIP, String HttpUrl)
	{
		try
		{
			addAliasIP(srcIP);
			
			/*URL url = new URL("http://172.17.2.2/ResponseServlet");
			URLConnection hrlConnection = url.openConnection();*/
			
			addAliasIP(srcIP);																			 
			URI uri = new URI(HttpUrl);
			String host = uri.getHost();
			String path = uri.getRawPath();
			
			if(path == null || path.length() == 0)
			{
				path = "/";
			}
	
			String query = uri.getRawQuery();
			if(query != null && query.length() > 0)
			{
				path += "?" + query;
			}
	
			String protocol = uri.getScheme();
			System.out.println("protocol: " + protocol);
			int port = uri.getPort();
			if(port == -1)
			{
				if(protocol.equals("http"))
				{
					port = 80; // http port
				}
				
				else if(protocol.equals("https"))
				{
					port = 443; // https port
				}
				
				else
				{
					return;
				}
			}
	
			InetAddress address = InetAddress.getByName(srcIP);
	
			Socket clientSocket = new java.net.Socket();
			clientSocket.bind(new InetSocketAddress(address, 0));
			clientSocket.connect(new InetSocketAddress(host, port));
	
			PrintWriter request = new PrintWriter(clientSocket.getOutputStream());
			request.print("GET " + path + " HTTP/1.1\r\n" + "Host: " + host + "\r\n" + "Connection: close\r\n\r\n");
			request.flush();
	
			InputStream inStream = clientSocket.getInputStream();
	
			BufferedReader rd = new BufferedReader(new InputStreamReader(inStream));
	
			String line;
			while((line = rd.readLine()) != null)
			{
				System.out.println(line);
			}
	
			clientSocket.close();
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}

	public void addAliasIP(String IP)
	{
		try
		{
			String command = "ifconfig eth1:0 " + IP + " up";
			StringBuffer output = new StringBuffer();
	
			Process p;
	
			p = Runtime.getRuntime().exec(command);
			p.waitFor();
	
			BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
	
			String line = "";
			while((line = reader.readLine()) != null)
			{
				output.append(line + "\n");
			}
		}
		
		catch(Exception e)
		{
			e.printStackTrace();
		}

		// /System.out.println(output.toString());
	}
}
