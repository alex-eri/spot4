import struct
from .constants import *
from collections import defaultdict


def int32be(data):
    if len(data) == 4:
        return struct.unpack("!L",data)[0]

ipaddr = int32be

def string(data):
    return data.decode('utf-8')

def ascii(data):
    return data.decode('ascii')

def bytes(data):
    return data

def mac(data):
    return data.decode('ascii').upper().replace('-',':')

int = int32be
time = int32be

def default_decoder():
    return bytes

decoders = defaultdict(default_decoder, {
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
    CallingStationId  : mac,
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
    PortLimit : int,
    MikrotikHostIP: ipaddr,
    WISPrLocationName: string,
    ChilliSpotVersion: ascii,
    MSMPPEEncryptionPolicy: int
})
