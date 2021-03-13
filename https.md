Нужны сертификаты для 2х доменов:

hs1.eri.su - сервер
router.eri.su - роутер

Поставить nginx
apt install nginx

удалить /etc/nginx/sites-enabled/default

Добавить /etc/nginx/sites-enabled/spot4.conf

server {

        listen 80;
        listen [::]:80;
        listen 443 ssl;
        listen [::]:443 ssl;
        ssl_certificate /etc/letsencrypt/live/hs1.eri.su/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/hs1.eri.su/privkey.pem;
        include /etc/nginx/snippets/ssl-params.conf;

        server_name hs1.eri.su;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host:$server_port;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /.well-known {
            root /var/www/;
    }
}

Где /etc/letsencrypt/live/hs1.eri.su/fullchain.pem и /etc/letsencrypt/live/hs1.eri.su/privkey.pem пути к сертификатам и ключам.


Генерируем профиль с доменом и https

make -C /opt/spot4/mikrotik IP=hs1.eri.su PORT=443 PROTO=https


Установить сертификат на роутер

Предположим, сертификат у вас уже имеется. Первым делом копируем файл сертификата (с расширением *.cer) и приватный ключ (с расширением *.key) в память Mikrotik. Далее идем в System – Certificates, выполняем импорт файлов. Сначала импортируем файл *.cer, при этом у сертификата появится признак «CRL» и «trusted».

Затем импортируем *.key, после чего на сертификате добавится статус «private key».

То же самое можно выполнить при помощи командной строки:
/certificate import file-name=router.eri.su.cer
/certificate import file-name=router.eri.su.key

В хотспоте включаете https и указвайте сертификат, переставьте профиль на новый. DNS Name указать router.eri.su и можно добавить в dns static на внутренний адрес роутера.


