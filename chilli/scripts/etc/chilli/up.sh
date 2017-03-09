#!/bin/sh

TUNTAP=$(basename $DEV)
UNDO_FILE=/var/run/chilli.$TUNTAP.sh

[ -e "$UNDO_FILE" ] && sh $UNDO_FILE 2>/dev/null
rm -f $UNDO_FILE 2>/dev/null

ipt() {
    opt=$1; shift
    echo "iptables -D $*" >> $UNDO_FILE
    iptables $opt $*
}

ipt_in() {
    ipt -I INPUT -i $TUNTAP $*
}

run_up() {
    if [ -n "$TUNTAP" ]
    then
        # ifconfig $TUNTAP mtu $MTU
	if [ "$KNAME" != "" ]
	then
	    ipt -I FORWARD -i $DHCPIF -m coova --name $KNAME -j forwarding_rule
	    ipt -I FORWARD -o $DHCPIF -m coova --name $KNAME --dest -j forwarding_rule
	    ipt -I FORWARD -i $TUNTAP -j forwarding_rule
	    ipt -I FORWARD -o $TUNTAP -j forwarding_rule
	    [ -n "$DHCPLISTEN" ] && ifconfig $DHCPIF $DHCPLISTEN
	else
	    if [ "$LAYER3" != "1" ]
	    then
		[ -n "$UAMPORT" -a "$UAMPORT" != "0" ] && \
		    ipt_in -p tcp -m tcp --dport $UAMPORT --dst $ADDR -j ACCEPT

		[ -n "$UAMUIPORT" -a "$UAMUIPORT" != "0" ] && \
		    ipt_in -p tcp -m tcp --dport $UAMUIPORT --dst $ADDR -j ACCEPT

		[ -n "$HS_TCP_PORTS" ] && {
		    for port in $HS_TCP_PORTS; do
			ipt_in -p tcp -m tcp --dport $port --dst $ADDR -j ACCEPT
		    done
		}

		ipt_in -p udp -d 255.255.255.255 --destination-port 67:68 -j ACCEPT
		ipt_in -p udp -d $ADDR --destination-port 67:68 -j ACCEPT
		ipt_in -p udp --dst $ADDR --dport 53 -j ACCEPT
		ipt_in -p icmp --dst $ADDR -j ACCEPT

		ipt -A INPUT -i $TUNTAP --dst $ADDR -j DROP

		if [ "$ONLY8021Q" != "1" ]
		then
		    ipt -I INPUT -i $DHCPIF -j DROP
		fi
	    fi

	    if [ "$ONLY8021Q" != "1" ]
	    then
		ipt -I FORWARD -i $DHCPIF -j DROP
		ipt -I FORWARD -o $DHCPIF -j DROP
	    fi

	    ipt -I FORWARD -i $TUNTAP -j forwarding_rule
	    ipt -I FORWARD -o $TUNTAP -j forwarding_rule

            # Help out conntrack to not get confused
            # (stops masquerading from working)
            #ipt -I PREROUTING -t raw -j NOTRACK -i $DHCPIF
            #ipt -I OUTPUT -t raw -j NOTRACK -o $DHCPIF

	    [ "$HS_LOCAL_DNS" = "on" ] && \
		ipt -I PREROUTING -t nat -i $TUNTAP -p udp --dport 53 -j DNAT --to-destination $ADDR
	fi
    fi

    # site specific stuff optional
    [ -e /etc/chilli/ipup.sh ] && . /etc/chilli/ipup.sh
}


FLOCK=$(which flock)
if [ -n "$FLOCK" ] && [ -z "$LOCKED_FILE" ]
then
    export LOCKED_FILE=/tmp/.chilli-flock
    flock -x $LOCKED_FILE -c "$0 $@"
else
    run_up
fi
