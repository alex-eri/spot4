 db.invoice.insert(
{
    "username" : db.users.findOne({with:"+79158327039"})["_id"],
    "paid" : true,
    "start" : new Date(),
    "stop" : new Date((new Date()).getTime() + 1000*60*60*1),
    "voucher" : true,
    "tarif" : true,
    "limit" : {
        "rate" :  NumberInt(10),
        "time" :  NumberInt(18600),
        "ports" :  NumberInt(3),
        "redir" : "http://wow.ru",
        "bytes": NumberInt(0),
    },
    "callee" : "server1"
}
)
