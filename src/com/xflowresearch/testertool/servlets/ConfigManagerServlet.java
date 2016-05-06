package com.xflowresearch.testertool.servlets;

import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONArray;
import org.json.JSONObject;

import java.sql.PreparedStatement;

@WebServlet("/config")
@SuppressWarnings("serial")
public class ConfigManagerServlet extends HttpServlet 
{    
    private boolean connectedToDb = false;
    private Connection conn = null;
    
    private void connectToDB()
    {
		if(!connectedToDb)
		{
			try
			{
				conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/testertool", "tt_admin", "testertool");
				connectedToDb = true;
			}
			 
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
    }
    
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{	
		connectToDB();
		
		String action = null;
		
		try
		{
			action = request.getParameter("action");
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
		}
		
		if(action.equals("getNames"))
		{
			try
			{
				Statement st = conn.createStatement();
				ResultSet rs = st.executeQuery("select name from testertool.configurations");
				
				JSONArray jArray = new JSONArray();
				
				while(rs.next())
				{
					JSONObject jObj = new JSONObject();
					jObj.put("name", rs.getString("name"));
					/*jObj.put("mcc", rs.getString("mcc"));
					jObj.put("mnc", rs.getString("mnc"));
					jObj.put("mme_ip", rs.getString("mme_ip"));
					jObj.put("mme_port", rs.getString("mme_port"));
					jObj.put("global_enbid", rs.getString("global_enbid"));
					jObj.put("enb_name", rs.getString("enb_name"));
					jObj.put("supported_tas", rs.getString("supported_tas"));
					jObj.put("default_pagingdrx", rs.getString("default_pagingdrx"));
					jObj.put("tai", rs.getString("tai"));
					jObj.put("eutrancgi", rs.getString("eutrancgi"));
					jObj.put("returnIP", rs.getString("returnIP"));
					jObj.put("rrc_estb_cause", rs.getString("rrc_estb_cause"));
					jObj.put("apn_name", rs.getString("apn_name"));
					jObj.put("webserver_ip", rs.getString("webserver_ip"));*/
					
					jArray.put(jObj);
				}
				
				jArray.write(response.getWriter());
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
		
		else if(action.equals("getByName"))
		{
			try
			{
				String name = request.getParameter("name");

				Statement st = conn.createStatement();
				ResultSet rs = st.executeQuery("select * from testertool.configurations where name = '" + name + "'");
				JSONObject jObj = new JSONObject();

				if(rs.next())
				{
					jObj.put("result", true);
					jObj.put("name", rs.getString("name"));
					jObj.put("mcc", rs.getString("mcc"));
					jObj.put("mnc", rs.getString("mnc"));
					jObj.put("mme_ip", rs.getString("mme_ip"));
					jObj.put("mme_port", rs.getString("mme_port"));
					jObj.put("global_enbid", rs.getString("global_enbid"));
					jObj.put("enb_name", rs.getString("enb_name"));
					jObj.put("supported_tas", rs.getString("supported_tas"));
					jObj.put("default_pagingdrx", rs.getString("default_pagingdrx"));
					jObj.put("tai", rs.getString("tai"));
					jObj.put("eutrancgi", rs.getString("eutrancgi"));
					jObj.put("returnIP", rs.getString("returnIP"));
					jObj.put("rrc_estb_cause", rs.getString("rrc_estb_cause"));
					jObj.put("apn_name", rs.getString("apn_name"));
					jObj.put("webserver_ip", rs.getString("webserver_ip"));
					
					jObj.write(response.getWriter());
				}
				
				else
				{
					jObj.put("result", false);
					jObj.write(response.getWriter());
				}
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}
	}

	private boolean insert(HttpServletRequest request)
	{
		try
		{
			PreparedStatement prepStmnt = conn.prepareStatement("insert into testertool.configurations (name, mcc, mnc, mme_ip, mme_port, global_enbid, enb_name, "
					+ "supported_tas, default_pagingdrx, tai, eutrancgi, returnIP, rrc_estb_cause, apn_name, webserver_ip) "
					+ "values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
			
			prepStmnt.setString(1, request.getParameter("name"));
			prepStmnt.setString(2, request.getParameter("mcc"));
			prepStmnt.setString(3, request.getParameter("mnc"));
			prepStmnt.setString(4, request.getParameter("mme_ip"));
			prepStmnt.setString(5, request.getParameter("mme_port"));
			prepStmnt.setString(6, request.getParameter("global_enbid"));
			prepStmnt.setString(7, request.getParameter("enb_name"));
			prepStmnt.setString(8, request.getParameter("supported_tas"));
			prepStmnt.setString(9, request.getParameter("default_pagingdrx"));
			prepStmnt.setString(10, request.getParameter("tai"));
			prepStmnt.setString(11, request.getParameter("eutrancgi"));
			prepStmnt.setString(12, request.getParameter("returnIP"));
			prepStmnt.setString(13, request.getParameter("rrc_estb_cause"));
			prepStmnt.setString(14, request.getParameter("apn_name"));
			prepStmnt.setString(15, request.getParameter("webserver_ip"));
			
			prepStmnt.executeUpdate();
			return true;
		}
		
		catch(Exception exc)
		{
			exc.printStackTrace();
			return false;
		}
	}
	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
		connectToDB();
		
		String action = request.getParameter("action");
		System.out.println("POST request received");
		
		if(action.equals("createNew"))
		{			
			try
			{								
				if(insert(request))
					response.getWriter().write("Successfully added new configuration.");
				
				else
					response.getWriter().write("Failed to add new configuration.");
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
			}
		}

		else if(action.equals("edit"))
		{
			try
			{
				String name = request.getParameter("name");
		
				PreparedStatement prepStmnt = conn.prepareStatement("delete from testertool.configurations where name = ?");
				prepStmnt.setString(1, name);
				prepStmnt.executeUpdate();
				
				insert(request);
				
				response.getWriter().write("Successfully changed configuration.");
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
				response.getWriter().write("Failed to change configuration.");
			}
		}
		
		else if(action.equals("delete"))
		{
			try
			{
				String name = request.getParameter("name");
		
				PreparedStatement prepStmnt = conn.prepareStatement("delete from testertool.configurations where name = ?");
				prepStmnt.setString(1, name);				
				prepStmnt.executeUpdate();
				
				response.getWriter().write("Successfully deleted configuration.");
			}
			
			catch(Exception exc)
			{
				exc.printStackTrace();
				response.getWriter().write("Failed to delete configuration.");
			}
		}
	}
}