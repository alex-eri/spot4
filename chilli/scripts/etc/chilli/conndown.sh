#!/bin/sh

remove_filter() {
    /usr/sbin/iptables -D forwarding_rule -s ${FRAMED_IP_ADDRESS} -j ${FILTER_ID}
}

[ "x${FILTER_ID}" == "x" ] && remove_filter
