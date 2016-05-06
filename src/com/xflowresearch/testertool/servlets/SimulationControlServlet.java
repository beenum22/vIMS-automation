package com.xflowresearch.testertool.servlets;

import java.io.IOException;
import java.util.ArrayList;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.xflowresearch.nfv.testertool.common.ConfigHandler;
import com.xflowresearch.nfv.testertool.enodeb.eNodeB;
import com.xflowresearch.nfv.testertool.ue.UE;
import com.xflowresearch.nfv.testertool.ue.UEController;

@WebServlet("/control")
@SuppressWarnings("serial")
public class SimulationControlServlet extends HttpServlet
{
	ArrayList<UE> UEs;
	ArrayList<eNodeB> eNodeBs;

	ConfigHandler configHandler;

	UEController ueController;

	@Override
	public void init() throws ServletException
	{
		try
		{
			UEs = new ArrayList<>();
			eNodeBs = new ArrayList<>();

			configHandler = new ConfigHandler();
			getServletContext().setAttribute("xmlparser", configHandler);

			ueController = new UEController(configHandler, eNodeBs);
			ueController.startGtpListener();
			getServletContext().setAttribute("uecontroller", ueController);
			
			if(configHandler.connectToDB())
			{
				//configHandler.readIMSIParamters();
				System.out.println("Connected to database...");
			}
			
			else
			{
				System.out.println("Failed to establish connection with the database!");
				System.exit(-1);
			}
		}

		catch(Exception exc)
		{
			exc.printStackTrace();
		}

		super.init();
	}

	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException
	{
		
	}
		
	@Override
	protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException
	{
		System.out.println("POST request received");
		
		if(req.getParameter("action").equals("setConfig"))
		{
			String nameOfConfig = req.getParameter("name");
			
			if(configHandler.getConfigFromDB(nameOfConfig))
			{
				resp.getWriter().write("success");
			}
			
			else resp.getWriter().write("failure");
		}
		
		else if(req.getParameter("action").equals("launch_enb"))
		{
			eNodeB meNodeb = new eNodeB(configHandler, ueController);
			eNodeBs.add(meNodeb);
			if(meNodeb.establishS1Signalling())
			{
				resp.getWriter().write("success");
			}
			
			else
			{
				resp.getWriter().write("failed");
			}
		}
		
		else if(req.getParameter("action").equals("create_ue"))
		{
			int N = Integer.parseInt(req.getParameter("param2"));
			System.out.println("N: " + N);
			
			configHandler.readIMSIParamters(N);

			for(int i = 0; i < N; i++)
			{
				UEs.add(new UE(i, configHandler.getUEParameters(i), configHandler, ueController));
			}
						
			resp.getWriter().write("success");
		}
		
		else if(req.getParameter("action").equals("launch_ue"))
		{
			String result = UEs.get(Integer.parseInt(req.getParameter("param2"))).attach();
			
			if(!result.equals("failed"))
			{
				resp.getWriter().write(result);
			}
			
			else
			{
				resp.getWriter().write("failed");
			}
		}
		
		else if(req.getParameter("action").equals("launch_http"))
		{
			String id = req.getParameter("param2");
			System.out.println("id: " + id);
			
			resp.getWriter().write(ueController.doHttp(id));
		}
	}
}
