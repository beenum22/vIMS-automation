<%@page import="java.util.Date"%>
<%@ page language="java" contentType="text/html; charset=ISO-8859-1"
	pageEncoding="ISO-8859-1"%>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
	<head>
		<style type="text/css">
		
			label
			{
			    display: inline-block;
			    float: left;
			    clear: left;
			    width: 130px;
			    text-align: right;
			}
			
			input 
			{
			  display: inline-block;
			  float: left;
			}
		</style>
		
		<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
		<title>Insert title here</title>
	</head>
	
	<body>
		<h1>Tester Tool</h1>
		
		<div>
	        <form action="control" method="post">
	           <label>Number of UEs: </label>	  <input type = "text" name="no_of_ues">  <br><br>
	           <label>Number of eNodeBs: </label> <input type = "text" name="no_of_enbs"> <br><br>
	           
	           <input type = "submit" value = "Launch">
	        </form>
        </div>
		
	</body>
</html>