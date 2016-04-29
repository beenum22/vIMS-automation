package com.xflowresearch.nfv.testertool.common;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;

public class IMSIParser
{
	BufferedReader inputReader;	
	PrintWriter outputWriter;
	private int totalItems;
	
	private void createEntry(String tag, String value)
	{
		outputWriter.write("\t<" + tag + ">" + value + "</" + tag + ">\n\n");		
		outputWriter.flush();
	}
	
	private void createIMSIEntry(String IMSI, String K)
	{
		outputWriter.write("\t<Value>\n\t\t<IMSI>"  + IMSI + "</IMSI>\n\t\t<K>" + K + "</K>\n\t</Value>\n\n");
		outputWriter.flush();
	}
	
	public void createIMSIFile(String inputFile, String outputFile)
	{
		try
		{
			inputReader = new BufferedReader(new FileReader(new File(inputFile)));
			outputWriter = new PrintWriter(new File(outputFile));
			
			outputWriter.write("<UEParams>\n\n");
			outputWriter.flush();
			
			totalItems = Integer.parseInt(inputReader.readLine().split(" ")[1]);
			createEntry("TotalItems", Integer.toString(totalItems));
			//System.out.println(totalItems);
			
			String line = inputReader.readLine();
			createEntry("OP", line.split(" ")[3].substring(32));
			createIMSIEntry(line.split(" ")[1], line.split(" ")[3].substring(0, 32));

			while((line = inputReader.readLine()) != null)
			{
				createIMSIEntry(line.split(" ")[1], line.split(" ")[3].substring(0, 32));
			}
			
			outputWriter.write("</UEParams>");
			outputWriter.flush();
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
	}
	
	public int getTotalItems()
	{
		return totalItems;
	}
}
