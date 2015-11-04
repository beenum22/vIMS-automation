//NAC PROTOCOL DEFINITIONS

package com.xflowresearch.nfv.testertool.ue.nas;
public class NASDefinitions {

		public enum MobilityManagementMessageType
		//for the case when Protocol Discriminator = EPS Mobility Management Message
		{
			AttachRequest("01000001"),
			AttachAccept("42"),
			AttachComplete("43"),
			AttachReject("44"),
			DetachRequest("45"),
			DetachAccept("46"),
			TrackingAreaUpdateRequest("48"),
			TrackingAreaUpdateAccept("49"),
			TrackingAreaUpdateComplete("4A"),
			TrackingAreaUpdateReject("4B"),
			ExtendedServiceRequest("4C"),
			ServiceReject("4D"),
			GUTIReallocationCommand("50"),
			GUTIReallocationComplete("51"),
			AuthenticationRequest("52"),
			AuthenticationResponse("01010011"),
			AuthenticationReject("54"),
			AuthenticationFailure("5C"),
			IdentityRequest("55"),
			IdentityResponse("56"),
			SecurityModeCommand("5D"),
			SecurityModeComplete("5E"),
			SecurityModeReject("5F"),
			EMMStatus("60"),
			EMMInformation("61"),
			DownlinkNASTransport("62"),
			UplinkNASTransport("63"),
			CSServiceNotification("64"),
			DownlinkGenericNASTransport("68"),
			UplinkGenericNASTransport("69");
			
			private String hexValue;
			
	
			private MobilityManagementMessageType(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			public static String hexToType(String hexVal){
				if (hexVal != null) {
					for (MobilityManagementMessageType b : MobilityManagementMessageType.values()) {
						if (hexVal.equalsIgnoreCase(b.getHexCode())) {
							return b.toString();
						}
					}
				}
				return null;
			}
			
			
		}
		
		
		public enum EPSSessionManagementMessageType{  ////for the case when Protocol Discriminator = EPS Session Management Message Type
			
			ActivateDefaultEPSBearerContextRequest(""),
			ActivateDefaultEPSBearerContextAccept(""),
			ActivateDefaultEPSbearerContextReject(""),
			ActivateDedicatedEPSbearerContextRequest(""),
			ActivateDedicatedEPSbearerContextAccept(""),
			ActivateDedicatedEPSbearercontextAeject(""),
			ModifyEPSBearercontextrequest(""),
			ModifyEPSBearercontextaccept(""),
			ModifyEPSBearercontextreject(""),
			DeactivateEPSBearercontextrequest(""),
			DeactivateEPSBearerContextaccept(""),
			PDNconnectivityRequest(""),
			PDNconnectivityReject(""),
			PDNdisconnectRequest(""),
			PDNdisconnectReject(""),
			BearerresourceAllocationRequest(""),
			Bearerresourceallocationreject(""),
			Bearerresourcemodificationrequest(""),
			Bearerresourcemodificationreject(""),
			ESMinformationrequest(""),
			ESMInformationResponse("DA"),
			Notification(""),
			ESMstatus("");
			
			
			private String hexValue;
			
			
			private EPSSessionManagementMessageType(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			public static String hexToType(String hexVal){
				if (hexVal != null) {
					for (EPSSessionManagementMessageType b : EPSSessionManagementMessageType.values()) {
						if (hexVal.equalsIgnoreCase(b.getHexCode())) {
							return b.toString();
						}
					}
				}
				return null;
			}
			
			
		}
	
		
		
		
		public enum SecurityHeaderType
		{
			PlainNASMessage("0000"),
			IntegrityProtected("0001"),
			IntegrityProtectedCiphered("0010"),
			IntegrityProtectedwithnewEPSSecurityContext("0011"),
			ServiceRequestMessageSecurityHeader("1000"),
			SecurityheaderforServiceRequest("1100");
			
			//1100, 1111 These values are not used in this version of the protocol.
			//to If received they shall be interpreted as '1100'. )
			
			
			private String hexValue;
			
			
			private SecurityHeaderType(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			public static String hexToType(String hexVal){
				if (hexVal != null) {
					for (SecurityHeaderType b : SecurityHeaderType.values()) {
						if (hexVal.equalsIgnoreCase(b.getHexCode())) {
							return b.toString();
						}
					}
				}
				return null;
			}
			
		}
		
		
	
		
		public enum ProtocolDiscriminatorValue{
			
			GroupCallControl("0000"),
			BroadcastCallControl("0001"),
			EPSSessionManagementMessage("0010"),
			CallControl("0011"),
			GTTP("0100"),
			MobilityManagementMessage("0101"),
			RRMMessage("0110"),
			EPSMobilityManagementMessage("0111"),
			GPRSMobilityManagementMessage("1000"),
			SMSMessage("1001"),
			GPRSSessionManagementMessage("1010"),
			NonCallRelatedSSMessage("1011"),
			LocationService("1100"),
			ReservedforExtensionofPDtoOneOctetLength("1110"),
			UsedByTestProcedure("1111");
			
			private String hexValue;
			
			
			private ProtocolDiscriminatorValue(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			
			public static String hexToType(String hexVal){
				if (hexVal != null) {
					for (ProtocolDiscriminatorValue b : ProtocolDiscriminatorValue.values()) {
						if (hexVal.equalsIgnoreCase(b.getHexCode())) {
							return b.toString();
						}
					}
				}
				return null;
			}
		}
		
		
		
		public enum TypeofSecurityContextFlag{       //4th bit in the octet
			
			NativeSecurityContext("0"),
			MappedSecurityContext("1");
			
			
			
			private String hexValue;
			private TypeofSecurityContextFlag(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			
			
			//TSC does not apply for NAS key set identifier value "7".
		}
		
		
		
		public enum KeySetIdentifier
		{
	
			NoKeyAvailable ("111");
			
			private String hexValue;
			
			private KeySetIdentifier(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
		}
		
		
		public enum SpareBit
		{
			Spare("0");
			
			private String hexValue;
			
			private SpareBit(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
		}
		
		
		public enum EPSAttachType{
			
			EPSAttach("001"),
			CombinedEPSIMSIAttach("010"),
			EPSEmergencyAttach("110"),
			Reserved("7");
			//All other values are unused and shall be interpreted as "EPS attach", if received by the network
			
			private String hexValue;
			
			private EPSAttachType (final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
			public static String hexToType(String hexVal){
				if (hexVal != null) {
					for (EPSAttachType b : EPSAttachType
							.values()) {
						if (hexVal.equalsIgnoreCase(b.getHexCode())) {
							return b.toString();
						}
					}
				}
				return null;
			}
			
			
			
			
		}
		
		
		public enum TypeofIdentity
		{
			IMSI("1"),
			GUTI("2"),
			IMEI("3");
			
			//All other values are reserved
			
			private String hexValue;
			
			private TypeofIdentity (final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
		}
		
		
		
		public enum OddEvenIndication{
			
			odd("0"),
			even("1");
			
			private String hexValue;
			private OddEvenIndication(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
		}
		
		
		
		//NAS Security algorithms information elements
		public enum TypeofIntegrityProtectionAlgorithm {
			EIA0("0"),
			EIA1("1"),
			EIA2("2"),
			EIA3("3"),
			EIA4("5"),
			EIA5("6"),
			EIA6("7"),
			EIA7("8");
			

			private String hexValue;
			
			private TypeofIntegrityProtectionAlgorithm (final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
		}
		
		public enum TypeofCipheringAlgorithm {
			EEA0("0"),
			EEA1("1"),
			EEA2("2"),
			EEA3("3"),
			EEA4("5"),
			EEA5("6"),
			EEA6("7"),
			EEA7("8");
			
			
			private String hexValue;
			
			private TypeofCipheringAlgorithm (final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
		}
		
		public enum TMSIStatusBit{
			
			NoValidTMSIavailable("0"),
			ValidTMSIavailable("1");
			
			private String hexValue;
			
			private TMSIStatusBit(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
			
		}
		
		
		public enum EPSBearerIdentity{
			
			NoEPSBearerIdentityAssigned("0000");
			
            private String hexValue;
			
			private EPSBearerIdentity(final String hexValue) {
				this.hexValue = hexValue;
			}
			
			public String getHexCode(){
				return hexValue;
			}
		}
		
	
		
}
	