package com.xflowresearch.nfv.testertool.ue;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.Socket;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.UnknownHostException;
import java.util.Enumeration;

public class HTTPClient 
{

	public void sendRequest(String srcIP) throws URISyntaxException, UnknownHostException, IOException
	{
		addALiasIP(srcIP);
		/*
		 * To begin, you need to parse the given URL request to extract
		 *  the host, path, port, and protocol (i.e., HTTP, HTTPS, and 
		 *  so on). For example, let's parse the host and path first:
		 */
		String urlStr = "http://www.drdobbs.com/jvm/making-http-requests-from-java/240160966"; // some URL
		URI uri = new URI( urlStr); 
		String host = uri.getHost( ); 
		String path = uri.getRawPath( ); 
		if (path == null || path.length( ) == 0) {
			path = "/";
		} 

		String query = uri.getRawQuery( ); 
		if (query != null && query.length( ) > 0) {
			path += "?" + query;
		} 


		/*
		 * Next, let's extract the protocol and port, and make sure they match
		 */
		String protocol = uri.getScheme( ); 
		int port = uri.getPort( ); 
		if (port == -1) {
			if (protocol.equals("http")) { 
				port = 80; // http port 
			}
			else if (protocol.equals("https")) {
				port = 443; // https port 
			}
			else {
				return;
			}
		}


		NetworkInterface nif = NetworkInterface.getByName("eth0");
		Enumeration<InetAddress> nifAddresses = nif.getInetAddresses();


		InetAddress address = null;	
		//		while(nifAddresses.hasMoreElements()){
		//			address = nifAddresses.nextElement();
		//			String stringAddr = address.getHostAddress();
		//			System.out.println(stringAddr);
		//		}
		//		address = nifAddresses.nextElement();
		//		address = nifAddresses.nextElement();
		//		System.out.println(address);

		/*
		 *Now that the required information has been extracted, we need to do three
		 *main things. First, make a socket connection to the server; second, send
		 *a correctly formatted HTTP request; third, listen for the response. 
		 *Connecting is simple; just create a new Java Socket with the host and port: 
		 */
		//Socket clientSocket = new Socket(host, port, InetAddress.getByName("192.168.100.10"), 0);

		address = InetAddress.getByName(srcIP);

		Socket clientSocket = new java.net.Socket();
		clientSocket.bind(new InetSocketAddress(address, 0));
		clientSocket.connect(new InetSocketAddress("212.71.234.61", port));


		PrintWriter request = new PrintWriter( clientSocket.getOutputStream() );
		request.print(  "GET " + path + " HTTP/1.1\r\n" + 
				"Host: " + host + "\r\n" + 
				"Connection: close\r\n\r\n"); 
		request.flush();

		InputStream inStream = clientSocket.getInputStream();

		BufferedReader rd = new BufferedReader(
				new InputStreamReader(inStream));

		String line;
		while ((line = rd.readLine()) != null) {
			System.out.println(line);
		}

		clientSocket.close();
	}

	public void addALiasIP(String IP)
	{
		String command = "ifconfig eth1:0 " + IP + " up";
		StringBuffer output = new StringBuffer();

		Process p;
		try {
			p = Runtime.getRuntime().exec(command);
			p.waitFor();

			BufferedReader reader = 
					new BufferedReader(new InputStreamReader(p.getInputStream()));

			String line = "";			
			while ((line = reader.readLine())!= null) {
				output.append(line + "\n");
			}

		} catch (Exception e) {
			e.printStackTrace();
		}

//		/System.out.println(output.toString());

	}
	
}
