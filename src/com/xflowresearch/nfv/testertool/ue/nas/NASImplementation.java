package com.xflowresearch.nfv.testertool.ue.nas;

import java.io.IOException;


public class NASImplementation {

private String AttachRequest;
private String AuthRequest;
private String AuthResponse;
private String AuthReject;
private String AuthFailure;
private String SecureModeCommand;
private String SecurityModeReject;
private String SecurityModeComplete;
private String AttachReject;
private String ESMInfoRequest;
private String ESMInfoResponse;
private String AttachComplete;

public void NASInit(String AttachReq, String AuthReq,String AuthResp,String AuthRej,String AuthFail,String SecureModeCmd,String SecurityModeRej,String SecurityModeComp,String AttachRej,String ESMInfoReq,String ESMInfoResp,String AttachComp)
{
	AttachRequest=AttachReq;
	AuthRequest=AuthReq;
	AuthReject=AuthRej;
	AuthFailure=AuthFail;
	AttachReject=AttachRej;
	SecureModeCommand=SecureModeCmd;
	SecurityModeReject=SecurityModeRej;
	ESMInfoRequest=ESMInfoReq;
	ESMInfoResponse=ESMInfoResp;
	AttachComplete=AttachComp;
	SecurityModeComplete=SecurityModeComp;
}

public void parametersetter(String Filepath) throws IOException{
	
	
    ReadFile Reader=new ReadFile();
	String Str=Reader.readCommands(Filepath);
	String [] Command=Str.split("\n");
	

	AttachRequest=Command[0];
	AuthRequest=Command[1];
	AuthResponse=Command[2];
	AuthReject=Command[3];
	AuthFailure=Command[4];
	SecureModeCommand=Command[5];
	SecurityModeReject=Command[6];
	SecurityModeComplete=Command[7];
	AttachReject=Command[8];
	ESMInfoRequest=Command[9];
	ESMInfoResponse=Command[10];
	AttachComplete=Command[11];
	
	
	//Debugging
	//System.out.println("debug test start");
	//System.out.println(Str);
	//System.out.println(AttachRequest);
	//System.out.println(AuthRequest);
	//System.out.println(AuthResponse);
	//System.out.println(AuthReject);
	//System.out.println("test ends");

}

 public String NASAttachRequest(String packetval)
	{
		
	
	 //String value1="710BF600F1100001011234567802C0C000050201D031D15200F1100001"; //representing a particular UE
		
	    String value1=packetval;
	    
	    String firstbyte=(NASDefinitions.SecurityHeaderType.PlainNASMessage.getHexCode()
				+ NASDefinitions.ProtocolDiscriminatorValue.EPSMobilityManagementMessage.getHexCode()); //first
	   
	    firstbyte='0'+Integer.toHexString(Integer.parseInt(firstbyte,2));
	   
		   
		String secondbyte= NASDefinitions.MobilityManagementMessageType.AttachRequest.getHexCode(); 
		
		secondbyte=Integer.toHexString(Integer.parseInt(secondbyte,2));
	    
	    String thirdByte=NASDefinitions.TypeofSecurityContextFlag.NativeSecurityContext.getHexCode()+ NASDefinitions.KeySetIdentifier.NoKeyAvailable.getHexCode()+
	    		NASDefinitions.SpareBit.Spare.getHexCode()+NASDefinitions.EPSAttachType.EPSAttach.getHexCode();   
	    
	    thirdByte= Integer.toHexString(Integer.parseInt(thirdByte,2));
	   
	
		String Packet = firstbyte +secondbyte +thirdByte + value1;
		return Packet;
	
		 //System.out.println( "Attach Request Packet:" + " " +Packet );
		}

 
 public String [] MMEResponseParser(String Response)
 {
	 String Responsebytefirst=Response.substring(0,2);
	 String Responsebytesecond=Response.substring(2,4 );
	 
	 String AuthRejPar,AuthFailPar,SecModeRejPar,AuthReqPar,SecModeCmdPar;
	 AuthRejPar=null; AuthFailPar=null;SecModeRejPar=null;AuthReqPar=null;SecModeCmdPar=null;
	
	 if(Responsebytefirst.equals("07")){

	 if (Responsebytesecond.equals("52")){
			 
			 AuthReqPar=Responsebytesecond;
			// Output[0]=AuthReqPar;
	 } 
	 if(Responsebytesecond.equals("54") )
	 {
		 AuthRejPar=Responsebytesecond;
		 //Output[1]=AuthRejPar;
	 }
	 else if (((Responsebytesecond.equals("5C"))||(Responsebytesecond.equals("5c"))))
	 {
		 AuthFailPar=Responsebytesecond;
		 //Output[2]=AuthFailPar;
	 }
	 else if (((Responsebytesecond.equals("5F"))||(Responsebytesecond.equals("5f"))))
	 {
		SecModeRejPar= Responsebytesecond;
		//Output[4]=SecModeRejPar;
	 }
	 
	 }
	 
	 else if (Responsebytesecond.equals("37")){
		 
		 String ResponsebyteEight=(Response.substring(15,17));
		 if(ResponsebyteEight.equals("93") )
		 {
			 SecModeCmdPar=ResponsebyteEight;
			 //Output[5]=SecModeCmdPar;
		 }
		 
	 }
	 String Output [] ={AuthRejPar,AuthFailPar,SecModeRejPar,AuthReqPar,SecModeCmdPar };//parameters to be set
	 return Output;
 }
 

 public String [] AttachRepParser(String Reply){
	 
	 String SecurityHeaderType=NASDefinitions.SecurityHeaderType.hexToType(Reply.substring(0,1 ));//SecurityHeaderType
	 System.out.println(Reply.substring(0,1 )); //debugging
	 
	 String ProtocolDiscriminator=NASDefinitions.ProtocolDiscriminatorValue.hexToType(Reply.substring(1,2 )); //PD
	 String EPSMobilityManagementMsg=NASDefinitions.MobilityManagementMessageType.hexToType(Reply.substring(2,4));//EPS Mobility Management Message
	 String AuthParameterRandValue=Reply.substring( 6,38); 
	 String AUTNvalue=Reply.substring(40);
	
	 String Output [] ={SecurityHeaderType,ProtocolDiscriminator,EPSMobilityManagementMsg,AuthParameterRandValue, };//parameters to be set
	 return Output;
		
		
 }
 
 
 
 
 public String NASAuthenticationResponse(String RES,String AuthRespLength)
 {
	 
	 String firstbyte=(NASDefinitions.SecurityHeaderType.PlainNASMessage.getHexCode()
			 + NASDefinitions.ProtocolDiscriminatorValue.EPSMobilityManagementMessage.getHexCode()); 
	 
	 firstbyte='0'+Integer.toHexString(Integer.parseInt(firstbyte,2));
	 
	 String secondbyte= NASDefinitions.MobilityManagementMessageType.AuthenticationResponse.getHexCode(); 
		
	 secondbyte=Integer.toHexString(Integer.parseInt(secondbyte,2));
	 
	 String AuthRespParameter= RES + AuthRespLength;
	 
	 
	 String Packet=firstbyte + secondbyte + AuthRespParameter;
	 
	 
	 //System.out.println( firstbyte );
	// System.out.println(secondbyte );
	// System.out.println(  AuthRespParameter );
	 System.out.println( "Authentication Response Packet:" + " " +Packet );
	 return Packet;
	 
 }

 
 public String NASSecurityModeComplete(String packetval)
 {
	 String value1=packetval;
	 
	 String Packet=(NASDefinitions.SecurityHeaderType.IntegrityProtectedwithnewEPSSecurityContext.getHexCode()
				+ NASDefinitions.ProtocolDiscriminatorValue.MobilityManagementMessage.getHexCode()
				+ NASDefinitions.MobilityManagementMessageType.SecurityModeComplete.getHexCode()
				+value1);
	
	 return Packet;
 }
 
 public String NASESMInformationResponse(String packetval)
 {
	    String MsgAuthCode = packetval.substring(0,8);
	    
	    String firstbyte=(NASDefinitions.SecurityHeaderType.IntegrityProtectedCiphered.getHexCode()
	    		+ NASDefinitions.ProtocolDiscriminatorValue.MobilityManagementMessage.getHexCode()); //first BYTE
	   
	    firstbyte='0'+Integer.toHexString(Integer.parseInt(firstbyte,2));
	    
		String Seqno =packetval.substring(8, 10);
		String Byte2 =NASDefinitions.EPSBearerIdentity.NoEPSBearerIdentityAssigned.getHexCode()
				+NASDefinitions.ProtocolDiscriminatorValue.EPSSessionManagementMessage.getHexCode();
		Byte2='0'+Integer.toHexString(Integer.parseInt(Byte2,2));
		
		String ProcTransactionID=packetval.substring(10,12);
		
		
		
		String String1= NASDefinitions.SecurityHeaderType.PlainNASMessage.getHexCode()
				+ NASDefinitions.ProtocolDiscriminatorValue.EPSMobilityManagementMessage.getHexCode()
				+NASDefinitions.MobilityManagementMessageType.AttachComplete.getHexCode();
		
		
	     
	   String Packet= firstbyte + MsgAuthCode + Seqno + Byte2 + ProcTransactionID 
			   +NASDefinitions.EPSSessionManagementMessageType.ESMInformationResponse.getHexCode() +packetval.substring(16);
			   

		System.out.println(Packet);
		return Packet;
	}




 public String NASAttachComplete(String packetval)
	{
	
	   String MsgAuthCode = packetval.substring(2,10);
	    
	    String firstbyte=(NASDefinitions.SecurityHeaderType.IntegrityProtectedCiphered.getHexCode()
	    		+ NASDefinitions.ProtocolDiscriminatorValue.MobilityManagementMessage.getHexCode()); //first BYTE
	   
	    firstbyte='0'+Integer.toHexString(Integer.parseInt(firstbyte,2));
	    
		String Seqno =packetval.substring(8, 10);
		
		
		String String1= NASDefinitions.SecurityHeaderType.PlainNASMessage.getHexCode()
				+ NASDefinitions.ProtocolDiscriminatorValue.EPSMobilityManagementMessage.getHexCode()
				+NASDefinitions.MobilityManagementMessageType.AttachComplete.getHexCode();
		
		String ESMMsgContainer= packetval.substring(10);
	     
	   String Packet= firstbyte + MsgAuthCode + Seqno + String1 +ESMMsgContainer;

		System.out.println(Packet);
		return Packet;
	}
 

 public void runNASimulation() throws IOException{
 
	 //UE generated parameters 
     String Filepath="SuccessfulAttach.txt"	 ;
	 
	 String AttachReq=null;
	 String AuthReq=null;//from MME;
	 String AuthResp=null;
	 String AuthRej=null;
	 String AuthFail=null;
	 String SecureModeCmd=null;
	 String SecurityModeRej=null;
	 String AttachRej=null;
	 String ESMInfoReq=null;
	 String ESMInfoResp=null;
	 String AttachComplete=null;
	 String RES="634F82417968CA98"; //UE generated Authentication response parameter information element parameters : RES value and length of auth response
	 String AuthRespLength="8";
	 
	NASImplementation NASobject= new NASImplementation();
	
	NASobject.parametersetter(Filepath);
	//NASobject.NASInit(AttachReq, AuthReq, AuthRespLength, AuthRej, AuthFail, SecurityModeRej, SecureModeCmd, AttachRej, ESMInfoReq, ESMInfoResp, AttachComplete);//redundant
	
	 AttachReq=NASobject.AttachRequest;//include only the parts not in definitions
	 AuthReq=NASobject.AuthRequest;//include whole packet, will be EPC generated, only used at UE for checking
	 AuthResp=NASobject.AuthResponse;//include only parts not in definitons
	 AuthRej=NASobject.AuthReject;//complete packet,from MME,for checking
	 AuthFail=NASobject.AuthFailure;//complete packet,from MME,for checking
	 SecureModeCmd=NASobject.SecureModeCommand;//
	 SecurityModeRej=NASobject.SecurityModeReject;//complete,for checking
	 AttachRej=NASobject.AttachReject;
	 ESMInfoReq=NASobject.ESMInfoRequest;
	 ESMInfoResp=NASobject.ESMInfoResponse;
	 AttachComplete=NASobject.AttachComplete;
	 
	// System.out.println(AuthReq);
	  NASobject.NASAttachRequest(AttachReq);  
	 
	 /*//wait for MME response i.e.AuthReq message expected
	   System.out.println(AuthRej);
	   System.out.println(AuthFail);
	   System.out.println(AuthReq); *///Debugging Comments 
	 String [] ParserOutput;
	
	 
	 /*assuming no authentication reject message received.If however
	 an Authentication Reject message is received, the UE shall abort any EMM signalling procedure 
	 and enter state EMM-DEREGISTERED.*/
	 
	 if((NASobject.AuthReject.equals("null")&& (NASobject.AuthFailure.equals("null"))&& !(AuthReq.equals(null))))
	 {
		 
		 System.out.println("Authentication Request from UE :" + " " +NASobject.ESMInfoRequest);
		 NASobject.NASAuthenticationResponse(RES, AuthRespLength);
		 System.out.println("UE Authentication Response Sent to MME.");
		 
	 /*(When MME gets the authentication response message the MME compares the received RES value with the XRES (Expected Response) value. 
	 If RES == XRES, successful authentication*/
	 	 
	 }
	 
	// when AuthReq =null i.e. Auth Reject or Auth Failure
 
	 else if(!((AuthRej.equals("null"))) )
	 {
		 ParserOutput= NASobject.MMEResponseParser(NASobject.AuthReject);
		 if(ParserOutput[0].equals("54"))
		 {
			 //System.out.print(ParserOutput[0]);
			 System.out.println("Authentication not Completed.Authentication Reject Packet Received!");
		 }
		  
	 }
	 else if(!(AuthFail.equals("null")))
	 {
		 ParserOutput= NASobject.MMEResponseParser(AuthFail);
		 //System.out.print(ParserOutput[1]);                                  //Debugging Comment
		 if (((ParserOutput[1].equals("5C"))||(ParserOutput[1].equals("5c"))))
		 {
			 System.out.println("Authentication not Completed.Authentication Failure Packet Received!");
		 }
	 }
	 
	 //wait for security mode command from MME  
	 
	 
	 if (!(NASobject.SecurityModeReject.equals("null")))
	 {
		 ParserOutput= NASobject.MMEResponseParser(NASobject.SecurityModeReject);
		 if(ParserOutput[2].equals("5f")|| ParserOutput[2].equals("5F"))
		 {
		 System.out.println("Security Mode not completed.Security Mode Reject Message Received from MME.");
		 System.out.println("Security Mode Reject Packet:" + " " + NASobject.SecurityModeReject);	 
	 }
	 }
	 else if((NASobject.SecurityModeReject.equals("null"))&& !(NASobject.SecureModeCommand .equals(null)))
	 {
		
		 System.out.println("Secure Mode Command Received from MME:" + " " + NASobject.SecureModeCommand);
		 System.out.println ("Waiting for ESM information Request from MME...");
	 }
	 
	 
	 //wait for ESM Information Request from MME
	 
	 if (!(NASobject.ESMInfoRequest.equals("null")))
	 {
		 System.out.println("ESM Information Request Received from MME:" + "\n" + "ESM Info Request packet:" + " " + NASobject.ESMInfoRequest);
		 NASobject.NASESMInformationResponse(ESMInfoResp);  //send ESM Information Response
	 }

	 //Wait for attach Accept/Complete packet from MME
	 
	 
	 if(!(NASobject.AttachReject.equals("null")))
	 {
		 System.out.println("Attach Rejected");
	 }
	 else if(!(NASobject.AttachComplete.equals("null")) && NASobject.AttachReject.equals("null"))
	{
		System.out.println("UE attached succesfully:" ) ;
		System.out.print("Attach Complete Packet Received from UE:" + " " );
		NASobject.NASAttachComplete(AttachComplete);
		
	}
	
	
	 
 } 
} 

