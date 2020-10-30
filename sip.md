От провайдера телефонии получите логин/пароль или настройки регистрации

Устанавливаем asterisk и базовую конфигурацию

    apt install asterisk

в файле /etc/asterisk/manager.conf

    [general]
    enabled = yes
    port = 5038
    bindaddr = 0.0.0.0

    #include "manager.d/*.conf"


в файле /etc/asterisk/manager.d/admin.conf

    [spot]
    secret = aaeb4tF
    deny=0.0.0.0/0.0.0.0
    permit=127.0.0.1/255.255.255.255
    read = all
    write = all
    
в скобках логин, deny - запрещает удаленку, permit - разрешает ip по маске. NB! Этот интерфейс позволяет управлять вызовами.

В /etc/asterisk/extensions.conf добавьте входящий диалплан


    [sip-in]
    exten => _X.,1,NoOp("${CALLERID(num)} ${STRFTIME(${EPOCH},,%Y%m%d-%H%M%S)}")
     same => n,Wait(3)
     same => n,Hangup(21)






     
При подключении "провайдер к нам" (zadarma Example №2 (SIP URI)) в /etc/asterisk/sip.conf

    [zadarma]
    host=sipurifr.zadarma.com
    type=friend
    insecure=port,invite
    context=sip-in
    disallow=all
    allow=alaw
    allow=ulaw
    dtmfmode = auto
    directmedia=no
    nat=force_rport,comedia
    
 
    
    

При подключении по логину паролю в /etc/asterisk/sip.conf 

    [111111]
    host=sip.zadarma.com
    insecure=invite,port
    type=friend
    fromdomain=sip.zadarma.com
    disallow=all
    allow=alaw
    allow=ulaw
    dtmfmode=auto
    secret=password
    defaultuser=111111
    trunkname=111111
    fromuser=111111
    callbackextension=111111
    context=sip-in
    qualify=400
    directmedia=no
    nat=force_rport,comedia
    
где 111111 ваш внешний номер



    [rt]
    host={XX.XX.rt.ru}
    insecure=invite,port
    type=friend
    fromdomain={XX.XX.rt.ru}
    disallow=all
    allow=alaw
    allow=ulaw
    dtmfmode=auto
    secret={password}
    defaultuser={username}
    trunkname={201}
    fromuser={username}
    callbackextension={111111}
    context=sip-in
    qualify=400
    directmedia=no
    nat=force_rport,comedia

без {}, 201 - внутренний номер, 111111 - внешний(но можно внутренний) номер


Перезагрузите астериск.

    systemctl restart asterisk

Поставьте spot 298+, в конфигурации /opt/spot4/config/config.json добаьте блок

    "CALL":{
	    "enabled":true,
	    "pool": [

            {
            "driver": "ami",
            "numbers": ["+111111"],
            "host": "127.0.0.1",
            "username": "spot",
            "port": 5038,
            "reciever": true,
            "secret": "aaeb4tF",
            "timeout": 120
            }

	    ]
    },


timeout - сколько ждать звонка


для sms.ru

    {
        "driver":"smsru",
        "api_id":"13A687FF-DD79-BE25-388E-1E54FDBFEC84",
        "reciever": true
        }



