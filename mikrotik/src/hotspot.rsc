/radius
add address={IP} secret={SECRET} service=hotspot timeout=10s
/radius incoming
set accept=yes
/ip traffic-flow
set cache-entries=64k enabled=yes inactive-flow-timeout=5m
/ip traffic-flow target
add dst-address={IP} version=5 port=2055

/ip hotspot profile
add html-directory-override={PROTO}.{IP}.{PORT} login-by=http-chap,http-pap name=spot4 radius-interim-update=5m use-radius=yes

/ip hotspot
add address-pool=hotspotpool disabled=no idle-timeout=30m interface=hotspot keepalive-timeout=30m login-timeout=30m name=server1 profile=spot4

/ip hotspot user profile
add add-mac-cookie=no address-pool=hotspotpool keepalive-timeout=30m name=spot4 shared-users=3

/ip hotspot walled-garden
add dst-host={IP} dst-port={PORT}

/ip hotspot walled-garden ip
add action=accept disabled=no dst-address={IP} dst-port={PORT}

