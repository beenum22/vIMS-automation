package com.xflowresearch.nfv.testertool.ue.nas;


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;


public class ReadFile {
	
	private String Data;

	private String AttachRequest;
	private String AuthRequest;
	private String AuthResponse;
	private String AuthReject;
	private String AuthFailure;
	private String SecurityModeReject;
	private String SecureModeCommand;
	private String AttachReject;
	private String ESMInfoRequest;
	private String ESMInfoResponse;
	private String AttachComplete;
	
	public ReadFile()
	{
		Data=null;
	}
	String readCommands(String filename) throws IOException
	{	
		String str = null;
		 BufferedReader br = new BufferedReader(new FileReader(filename));
		    try {
		        StringBuilder sb = new StringBuilder();
		        String line = br.readLine();

		        while (line != null) {
		            sb.append(line);
		            sb.append("\n");
		            line = br.readLine();
		        }
		        str= sb.toString();
		    } 
		    catch(IOException e)
	         {
			    System.out.println("Exception Caught:"+e);
	         }
		    finally {
		        br.close();
		    }
			return str;
	      
	   }
	public static void main(String[] args) throws IOException {
		
		ReadFile Reader=new ReadFile();
		String Str=Reader.readCommands("C:/Users/kashmala/Desktop/parameters.txt");
		String [] strr=Str.split("\n");
		String str1=strr[10];
		System.out.print(str1);
	}

}
