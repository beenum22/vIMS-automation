package com.xflowresearch.nfv.testertool.enodeb.s1mme;


/**
 * S1APDefinitions
 * 
 *	S1APDefinitions class that contains all the 
 *	possible definitions required to create a 
 *	S1AP packet.
 *
 * 
 * @author ahmadarslan
 */
public class S1APDefinitions {

	public enum Type
	{
		InitiatingMessage("00"),
		SuccessfulOutcome ("20"),
		UnsuccessfulOutcome ("40");


		private String hexValue;

		private Type(final String hexValue) {
			this.hexValue = hexValue;
		}

		public String getHexCode(){
			return hexValue;
		}
		
		public static Type fromString(String text) {
			if (text != null) {
				for (Type b : Type.values()) {
					if (text.equalsIgnoreCase(b.toString())) {
						return b;
					}
				}
			}
			return null;
		}
		
		public static String hexToType(String hexVal){
			if (hexVal != null) {
				for (Type b : Type.values()) {
					if (hexVal.equalsIgnoreCase(b.getHexCode())) {
						return b.toString();
					}
				}
			}
			return null;
		}
	}

	public enum Criticality
	{
		reject("00"),
		ignore("40");


		private String hexValue;

		private Criticality(final String hexValue) {
			this.hexValue = hexValue;
		}

		public String getHexCode(){
			return hexValue;
		}
		
		public static Criticality fromString(String text) {
			if (text != null) {
				for (Criticality b : Criticality.values()) {
					if (text.equalsIgnoreCase(b.toString())) {
						return b;
					}
				}
			}
			return null;
		}
		
		public static String hexToCriticality(String hexVal){
			if (hexVal != null) {
				for (Criticality b : Criticality.values()) {
					if (hexVal.equalsIgnoreCase(b.getHexCode())) {
						return b.toString();
					}
				}
			}
			return null;
		}
	}


	public enum ProcedureCode
	{
		HandoverPreparation ("00"),
		HandoverResourceAllocation("01"),
		HandoverNotification("02"),
		PathSwitchRequest("03"),
		HandoverCancel("04"),
		ERABSetup("05"),
		ERABModify("06"),
		ERABRelease("07"),
		ERABReleaseIndication("08"),
		InitialContextSetup("09"),
		Paging("0A"),
		downlinkNASTransport("0B"),
		initialUEMessage("0C"),
		uplinkNASTransport("0D"),
		Reset("0E"),
		ErrorIndication("0F"),
		NASNonDeliveryIndication("10"),
		S1Setup("11"),
		UEContextReleaseRequest("12"),
		DownlinkS1cdma2000tunneling("13"),
		UplinkS1cdma2000tunneling("14"),
		UEContextModification("15"),
		UECapabilityInfoIndication("16"),
		UEContextRelease("17"),
		eNBStatusTransfer("18"),
		MMEStatusTransfer("19"),
		DeactivateTrace("1A"),
		TraceStart("1B"),
		TraceFailureIndication("1C"),
		ENBConfigurationUpdate("1D"),
		MMEConfigurationUpdate("1E"),
		LocationReportingControl("1F"),
		LocationReportingFailureIndication("20"),
		LocationReport("21"),
		OverloadStart("22"),
		OverloadStop("23"),
		WriteReplaceWarning("24"),
		eNBDirectInformationTransfer("25"),
		MMEDirectInformationTransfer("26"),
		PrivateMessage("27"),
		eNBConfigurationTransfer("28"),
		MMEConfigurationTransfer("29"),
		CellTrafficTrace("2A"),
		Kill("2B"),
		downlinkUEAssociatedLPPaTransport("2C"),
		uplinkUEAssociatedLPPaTransport("2D"),
		downlinkNonUEAssociatedLPPaTransport("2E"),
		uplinkNonUEAssociatedLPPaTransport("2F"),
		UERadioCapabilityMatch("30");


		private String hexValue;

		private ProcedureCode(final String hexValue) {
			this.hexValue = hexValue;
		}

		public String getHexCode(){
			return hexValue;
		}
		
		public static ProcedureCode fromString(String text) {
			if (text != null) {
				for (ProcedureCode b : ProcedureCode.values()) {
					if (text.equalsIgnoreCase(b.toString())) {
						return b;
					}
				}
			}
			return null;
		}
		
		public static String hexToProcedureCode(String hexVal){
			if (hexVal != null) {
				for (ProcedureCode b : ProcedureCode.values()) {
					if (hexVal.equalsIgnoreCase(b.getHexCode())) {
						return b.toString();
					}
				}
			}
			return null;
		}
	}

	/** TODO: Double check the Hex codes in IEDict **/
	public enum IEDict
	{
		MMEUES1APID ("00"),
		HandoverType("01"),
		Cause("02"),
		SourceID("03"),
		TargetID("04"),
		eNBUES1APID("08"),
		ERABSubjecttoDataForwardingList("0c"),
		ERABtoReleaseListHOCmd("0d"),
		ERABDataForwardingItem("0e"),
		ERABReleaseItemBearerRelComp("0f"),
		ERABToBeSetupListBearerSUReq("10"),
		ERABToBeSetupItemBearerSUReq("11"),
		ERABAdmittedList("12"),
		ERABFailedToSetupListHOReqAck("13"),
		ERABAdmittedItem("14"),
		ERABFailedtoSetupItemHOReqAck("15"),
		ERABToBeSwitchedDLList("16"),
		ERABToBeSwitchedDLItem("17"),
		ERABToBeSetupListCtxtSUReq("18"),
		TraceActivation("19"),
		NASPDU("1a"),
		ERABToBeSetupItemHOReq("1b"),
		ERABSetupListBearerSURes("1c"),
		ERABFailedToSetupListBearerSURes("1d"),
		ERABToBeModifiedListBearerModReq("1e"),
		ERABModifyListBearerModRes("1f"),
		ERABFailedToModifyList("20"),
		ERABToBeReleasedList("21"),
		ERABFailedToReleaseList("22"),
		ERABItem("23"),
		ERABToBeModifiedItemBearerModReq("24"),
		ERABModifyItemBearerModRes("25"),
		ERABReleaseItem("26"),
		ERABSetupItemBearerSURes("27"),
		SecurityContext("28"),
		HandoverRestrictionList("29"),
		UEPagingID("2b"),
		pagingDRX("2c"),
		TAIList("2e"),
		TAIItem("2f"),
		ERABFailedToSetupListCtxtSURes("30"),
		ERABReleaseItemHOCmd("31"),
		ERABSetupItemCtxtSURes("32"),
		ERABSetupListCtxtSURes("33"),
		ERABToBeSetupItemCtxtSUReq("34"),
		ERABToBeSetupListHOReq("35"),
		GERANtoLTEHOInformationRes("37"),
		UTRANtoLTEHOInformationRes("39"),
		CriticalityDiagnostics("3a"),
		GlobalENBID("3b"),
		eNBname("3c"),
		MMEname("3d"),
		ServedPLMNs("3f"),
		SupportedTAs("40"),
		TimeToWait("41"),
		uEaggregateMaximumBitrate("42"),
		TAI("43"),
		ERABReleaseListBearerRelComp("45"),
		cdma2000PDU("46"),
		cdma2000RATType("47"),
		cdma2000SectorID("48"),
		SecurityKey("49"),
		UERadioCapability("4a"),
		GUMMEIID("4b"),
		ERABInformationListItem("4e"),
		DirectForwardingPathAvailability("4f"),
		UEIdentityIndexValue("50"),
		cdma2000HOStatus("53"),
		cdma2000HORequiredIndication("54"),
		EUTRANTraceID("56"),
		RelativeMMECapacity("57"),
		SourceMMEUES1APID("58"),
		BearersSubjectToStatusTransferItem("59"),
		eNBStatusTransferTransparentContainer("5a"),
		UEassociatedLogicalS1ConnectionItem("5b"),
		ResetType("5c"),
		UEassociatedLogicalS1ConnectionListResAck("5d"),
		ERABToBeSwitchedULItem("5e"),
		ERABToBeSwitchedULList("5f"),
		STMSI("60"),
		cdma2000OneXRAND("61"),
		RequestType("62"),
		UES1APIDs("63"),
		EUTRANCGI("64"),
		OverloadResponse("65"),
		cdma2000OneXSRVCCInfo("66"),
		ERABFailedToBeReleasedList("67"),
		SourceToTargetTransparentContainer("68"),
		ServedGUMMEIs("69"),
		SubscriberProfileIDforRFP("6a"),
		UESecurityCapabilities("6b"),
		CSFallbackIndicator("6c"),
		CNDomain("6d"),
		ERABReleasedList("6e"),
		MessageIdentifier("6f"),
		SerialNumber("70"),
		WarningAreaList("71"),
		RepetitionPeriod("72"),
		NumberofBroadcastRequest("73"),
		WarningType("74"),
		WarningSecurityInfo("75"),
		DataCodingScheme("76"),
		WarningMessageContents("77"),
		BroadcastCompletedAreaList("78"),
		InterSystemInformationTransferTypeEDT("79"),
		InterSystemInformationTransferTypeMDT("7a"),
		TargetToSourceTransparentContainer("7b"),
		SRVCCOperationPossible("7c"),
		SRVCCHOIndication("7d"),
		NASDownlinkCount("7e"),
		CSGId("7f"),
		CSGIdList("80"),
		SONConfigurationTransferECT("81"),
		SONConfigurationTransferMCT("82"),
		TraceCollectionEntityIPAddress("83"),
		MSClassmark2("84"),
		MSClassmark3("85"),
		RRCEstablishmentCause("86"),
		NASSecurityParametersfromEUTRAN("87"),
		NASSecurityParameterstoEUTRAN("88"),
		DefaultPagingDRX("89"),
		SourceToTargetTransparentContainerSecondary("8a"),
		TargetToSourceTransparentContainerSecondary("8b"),
		EUTRANRoundTripDelayEstimationInfo("8c"),
		BroadcastCancelledAreaList("8d"),
		ConcurrentWarningMessageIndicator("8e"),
		DataForwardingNotPossible("8f"),
		ExtendedRepetitionPeriod("90"),
		CellAccessMode("91"),
		CSGMembershipStatus("92"),
		LPPaPDU("93"),
		RoutingID("94"),
		TimeSynchronizationInfo("95"),
		PSServiceNotAvailable("96"),
		PagingPriority("97"),
		x2TNLConfigurationInfo("98"),
		eNBX2ExtendedTransportLayerAddresses("99"),
		GUMMEIList("9a"),
		GWTransportLayerAddress("9b"),
		CorrelationID("9c"),
		SourceMMEGUMMEI("9d"),
		MMEUES1APID2("9e"),
		RegisteredLAI("9f"),
		RelayNodeIndicator("a0"),
		TrafficLoadReductionIndication("a1"),
		MDTConfiguration("a2"),
		MMERelaySupportIndicator("a3"),
		GWContextReleaseIndication("a4"),
		ManagementBasedMDTAllowed("a5"),
		PrivacyIndicator("a6"),
		TimeUEStayedInCellEnhancedGranularity("a7"),
		HOCause("a8"),
		VoiceSupportMatchIndicator("a9"),
		GUMMEIType("aa"),
		M3Configuration("ab"),
		M4Configuration("ac"),
		M5Configuration("ad"),
		MDTLocationInfo("ae"),
		MobilityInformation("af"),
		TunnelInformationforBBF("b0"),
		ManagementBasedMDTPLMNList("b1"),
		SignallingBasedMDTPLMNList("b2");

		private String hexValue;

		private IEDict(final String hexValue) {
			this.hexValue = hexValue;
		}

		public String getHexCode(){
			return hexValue;
		}

		public static IEDict fromString(String text) {
			if (text != null) {
				for (IEDict b : IEDict.values()) {
					if (text.equalsIgnoreCase(b.toString())) {
						return b;
					}
				}
			}
			return null;
		}
		
		public static String hexToIEDict(String hexVal){
			if (hexVal != null) {
				for (IEDict b : IEDict.values()) {
					if (hexVal.equalsIgnoreCase(b.getHexCode())) {
						return b.toString();
					}
				}
			}
			return null;
		}

	}


}
