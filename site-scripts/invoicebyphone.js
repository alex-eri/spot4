
use spot4;
db.friends.find().forEach(function(u) { 
db.invoice.insert(
    {
            'callee': "server1",
            'username': db.users.findOne({with:u.phone})["_id"],
            'paid': true,
            'start': new Date(),
            'stop': new Date((new Date()).getTime() + 1000*60*60*24*7),
            'limit': {
                'rate': 10,
                'ports': 5,
                'bytes': 0,
                'redir': "http://provider.ru/privet_klient.html",
                'time': 0,
            }
    })
})

