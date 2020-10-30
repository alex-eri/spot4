OSS


https
===


На сервере:
открыть порты 443 и 80 наружу

```
export HOTSPOTHOSTNAME=portal.eri.su
export ROUTERHOSTNAME=router.eri.su
export SECRET=`dd if=/dev/urandom bs=18 count=1| base64`

mkdir -p /var/www/.well-known/

apt install -y nginx certbot

systemctl stop nginx

certbot certonly --non-interactive --agree-tos --standalone -d $HOTSPOTHOSTNAME
certbot certonly --non-interactive --agree-tos --standalone -d $ROUTERHOSTNAME

mkdir -p /etc/nginx/snippets/
touch /etc/nginx/snippets/ssl-params.conf
rm /etc/nginx/sites-enabled/*

cat <<EOF>/etc/nginx/sites-enabled/spot4.conf
server {

        listen 80 default_server;
        listen [::]:80 default_server;
        listen 443 ssl default_server;
        listen [::]:443 ssl default_server;
        ssl_certificate /etc/letsencrypt/live/$HOTSPOTHOSTNAME/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$HOTSPOTHOSTNAME/privkey.pem;
        include /etc/nginx/snippets/ssl-params.conf;
        
        server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host:\$server_port;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /.well-known/ {
            root /var/www/.well-known/;
    }
}

EOF


systemctl start nginx

mkdir -p /opt/spot4/data/ssl/$SECRET
ln -s /etc/letsencrypt/live/router1.example.org/*.pem /opt/spot4/data/ssl/$SECRET/
make -C /opt/spot4/mikrotik PROTO=https IP=$HOTSPOTHOSTNAME PORT=443




```

на микротике


```
global HOTSPOTHOSTNAME "portal.eri.su"
global ROUTERHOSTNAME "router.eri.su"
global SECRET "KzjGgbbTXIhQ0KlU0Dbma0su"


/tool fetch dst-path=/flash/ url=https://$HOTSPOTHOSTNAME/data/ssl/$SECRET/privkey.pem
/tool fetch dst-path=/flash/ url=https://$HOTSPOTHOSTNAME/data/ssl/$SECRET/fullchain.pem

/certificate import file-name=flash/fullchain.pem name=hotspot passphrase="" 
/certificate import file-name=flash/privkey.pem name=hotspot passphrase="" 

/ip hotspot profile
add dns-name=router1.example.org html-directory=flash/hotspot \
    html-directory-override=flash/https.$HOTSPOTHOSTNAME.443 login-by=\
    mac,cookie,https,http-pap name=spot4https radius-interim-update=10m \
    ssl-certificate=hotspot use-radius=yes

/ip hotspot walled-garden ip
add action=accept disabled=no dst-address=212.60.5.161 

/ip hotspot
add disabled=no idle-timeout=none interface=guest name=server1 profile=spot4https

/system script
add dont-require-permissions=no name=updatessl owner=admin policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon \
    source="/tool fetch dst-path=/flash/ url=https://$HOTSPOTHOSTNAME/data/ssl/$SECRET/privkey.pem\r\
    \n/tool fetch dst-path=/flash/ url=https://$HOTSPOTHOSTNAME/data/ssl/$SECRET/fullchain.pem\r\
    \n\r\
    \n/certificate import file-name=flash/fullchain.pem name=hotspot passphrase=\"\" \r\
    \n/certificate import file-name=flash/privkey.pem name=hotspot passphrase=\"\" "

/system scheduler
add interval=1w name=schedule1 on-event=updatessl policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon

```
