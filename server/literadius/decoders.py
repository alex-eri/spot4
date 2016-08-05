import struct
from .constants import *

def ipaddr(datas):
    return [struct.unpack("!L",data)[0] for data in datas]

def string(datas):
    return [data.decode('utf-8') for data in datas]

def ascii(datas):
    return [data.decode('ascii') for data in datas]

def bytes(datas):
    return datas

def int(datas):
    return [struct.unpack("!L",data)[0] for data in datas]

def time(datas):
    return [struct.unpack("!L",data)[0] for data in datas]


decoders = {
    UserName : string,
    UserPassword : bytes,
    CHAPPassword : bytes,
    NASIPAddress : ipaddr,
    NASPort : int,
    ServiceType : int,
    FramedProtocol : int,
    FramedIPAddress : ipaddr,
    FramedIPNetmask : ipaddr,
    FramedRouting : int,
    ReplyMessage : string,
    State : bytes,
    Class : bytes,
    SessionTimeout : int,
    IdleTimeout : int,
    TerminationAction : int,
    CalledStationId : string,
    CallingStationId  : string,
    NASIdentifier : string,
    AcctStatusType : int,
    AcctDelayTime : int,
    AcctInputOctets : int,
    AcctOutputOctets : int,
    AcctSessionId : ascii,
    AcctAuthentic : int,
    AcctSessionTime : int,
    AcctInputPackets : int,
    AcctOutputPackets : int,
    AcctTerminateCause : int,
    AcctMultiSessionId : ascii,
    AcctLinkCount : int,
    AcctInputGigawords : int,
    AcctOutputGigawords : int,
    EventTimestamp : time,
    CHAPChallenge : bytes,
    NASPortType : int,
    PortLimit : int
}
