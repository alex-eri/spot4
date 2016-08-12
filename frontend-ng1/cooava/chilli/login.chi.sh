#!/bin/bash

env > /tmp/login.env
pwd >> /tmp/login.env

runlogin() {
    out=$($CHILLI_QUERY login sessionid "$COOVA_SESSIONID" username "$1" password "$2")
}


cat <<EOF
HTTP/1.1 200 OK
Content-Type: text/html
Set-Cookie: PORTAL_SESSIONID=$PORTAL_SESSIONID
Set-Cookie: COOVA_USERURL=$COOVA_USERURL
Connection: close
Cache: none

EOF

[ $AUTHENTICATED = 1 ] && logged_in="yes" || logged_in="no"

link_login_only="//${SERVER_NAME}/${REQUEST_URI}"

cat <<EOF
{
"mac":"${REMOTE_MAC}",
"username":"${CHI_USERNAME}",
"logged_in":"${logged_in}",
"error":"${error}",
"link_orig":"${link_orig}",
"link_redirect":"${link_redirect}",
"link_login_only":"${link_login_only}",
"link_logout":"${link_logout}",
"link_status":"${link_status}",
"hostname":"${SERVER_NAME}",
"chap_id":"${CHI_CHALLENGE:0:2}",
"chap_challenge":"${CHI_CHALLENGE:2}",
"uptime":"${uptime}",
"time_left":"${CHI_SESSION_TIMEOUT}"
}
EOF
