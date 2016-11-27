class typeofNAS():
    accend = 1
    wispr = 2
    mikrotik = 4
    chilli = 8


AccessRequest = 1
AccessAccept = 2
AccessReject = 3
AccountingRequest = 4
AccountingResponse = 5
AccessChallenge = 11
StatusServer = 12
StatusClient = 13
DisconnectRequest = 40
DisconnectACK = 41
DisconnectNAK = 42
CoARequest = 43
CoAACK = 44
CoANAK = 45

UserName = 1
UserPassword = 2
CHAPPassword = 3
NASIPAddress = 4
NASPort = 5
ServiceType = 6
FramedProtocol = 7
FramedIPAddress = 8
FramedIPNetmask = 9
FramedRouting = 10
FilterId = 11
FramedMTU = 12
FramedCompression = 13
LoginIPHost = 14
LoginService = 15
LoginTCPPort = 16
ReplyMessage = 18
CallbackNumber = 19
CallbackId = 20
FramedRoute = 22
FramedIPXNetwork = 23
State = 24
Class = 25
VendorSpecific = 26
SessionTimeout = 27
IdleTimeout = 28
TerminationAction = 29
CalledStationId = 30
CallingStationId = 31
NASIdentifier = 32
ProxyState = 33
LoginLATService = 34
LoginLATNode = 35
LoginLATGroup = 36
FramedAppleTalkLink = 37
FramedAppleTalkNetwork = 38
FramedAppleTalkZone = 39

AcctStatusType = 40
AcctDelayTime = 41
AcctInputOctets = 42
AcctOutputOctets = 43
AcctSessionId = 44
AcctAuthentic = 45
AcctSessionTime = 46
AcctInputPackets = 47
AcctOutputPackets = 48
AcctTerminateCause = 49
AcctMultiSessionId = 50
AcctLinkCount = 51
AcctInputGigawords = 52
AcctOutputGigawords = 53
EventTimestamp = 55

CHAPChallenge = 60
NASPortType = 61
PortLimit = 62

MessageAuthenticator = 80

NASPortId = 87

AscendDataRate = 197
AscendXmitRate = 255

AccountingStart	=		1
AccountingStop	=		2
AccountingUpdate	=	3
AccountingOn	=	7
AccountingOff	=	8


ChilliSpot = 14559
ChilliSpotMaxInputOctets = (ChilliSpot, 1)
ChilliSpotMaxOutputOctets = (ChilliSpot, 2)
ChilliSpotMaxTotalOctets = (ChilliSpot, 3)
ChilliSpotVersion = (ChilliSpot, 8)

CoovaChilliAcctViewPoint = (ChilliSpot, 10)

CoovaChilliNASViewPoint = NASViewPoint = 1
CoovaChilliClientViewPoint = ClientViewPoint = 2

CoovaChilliBandwidthMaxUp = (ChilliSpot, 4)
CoovaChilliBandwidthMaxDown = (ChilliSpot, 5)




WISPr = 14122
WISPrLocationName = (WISPr,2)
WISPrLogoffURL = (WISPr,3)
WISPrRedirectionURL = (WISPr,4)

WISPrBandwidthMaxUp = (WISPr, 7)
WISPrBandwidthMaxDown = (WISPr,8)

MT = Mikrotik = 14988
MikrotikRecvLimit = (Mikrotik,1)
MikrotikXmitLimit = (Mikrotik,2)
MikrotikRateLimit = (Mikrotik,8)
MikrotikHostIP = (Mikrotik,10)
MikrotikRecvLimitGigawords = (Mikrotik,14)
MikrotikXmitLimitGigawords = (Mikrotik,15)
MikrotikWirelessPSK = (Mikrotik, 16)
MikrotikAddressList = (Mikrotik,19 )


MS = Microsoft = 311
MSCHAPResponse = (Microsoft,1)
MSCHAPChallenge  = (Microsoft,11)
MSCHAPMPPEKeys =  (Microsoft,12)
MSCHAP2Response = (Microsoft,25)
MSCHAP2Success= (Microsoft,26)
MSMPPEEncryptionPolicy = (Microsoft,7)

#Acct-Terminate-Cause
TCUserRequest   =         1
TCLostCarrier   =         2
TCLostService   =         3
TCIdleTimeout   =         4
TCSessionTimeout=         5
TCAdminReset    =         6
TCAdminReboot   =         7
TCPortError     =         8
TCNASError      =         9
TCNASRequest    =         10
TCNASReboot     =         11
TCPortUnneeded  =         12
TCPortPreempted =         13
TCPortSuspended =         14
TCServiceUnavailable =    15
TCCallback      =          16
TCUserError     =         17
TCHostRequest   =         18
