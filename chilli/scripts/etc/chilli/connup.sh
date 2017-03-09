#!/bin/sh

#FRAMED_IP_ADDRESS
#FILTER_ID


remove_all() {
    /usr/sbin/iptables -nL forwarding_rule --line-numbers | \
        grep ${FRAMED_IP_ADDRESS} | \
        cut -f 1 -d " " | \
        xargs /usr/sbin/iptables -D forwarding_rule
    return 0
}

add_filter() {
    /usr/sbin/iptables -A forwarding_rule -s ${FRAMED_IP_ADDRESS} -j ${FILTER_ID}
}

[ "x${FILTER_ID}" == "x" ] && remove_filter || add_filter
