package com.xflowresearch.testertool.servlets;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.xflowresearch.nfv.testertool.simulationcontrol.SimulationControl;

@SuppressWarnings("serial")
public class ControlServlet extends HttpServlet
{

	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException
	{		
		
	}
	
	@Override
	protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException
	{
		int noOfUEs = Integer.parseInt(req.getParameter("no_of_ues"));
		int noOfeNBs = Integer.parseInt(req.getParameter("no_of_enbs"));
		
		new Thread(new Runnable()
		{
			public void run()
			{
				SimulationControl.getInstance().startSimulation(noOfUEs, 1);
			}
		}).start();
		
		resp.sendRedirect("index.jsp");
	}
}
