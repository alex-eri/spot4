
function zeroFill( number, width ) {
  width -= number.toString().length;
  if ( width > 0 )
  {
    return new Array( width + (/\./.test( number ) ? 2 : 1) ).join( '0' ) + number;
  }
  return number + ""; // always return a string
}

zeroFill(1,6)

db.devices.find({username: {$exists: false}}).forEach(function(i) { 

var n = 0
var ns = ''
var user = db.users.findOne({ with: i.phone })

if (user) {
  db.devices.update({_id: i._id},{ $set :{ username: user._id}})
} else {
  n = db.counters.findAndModify({query: {'_id':'userid'}, update:{ '$inc': { 'seq': 1 }}, new:true })
  ns = zeroFill(n.seq,6)
  db.users.insert( {with: i.phone , _id: ns} )
  user = db.users.findOne({ with: i.phone })
  print(user.with)
  db.devices.update({_id: i._id},{ $set :{ username: user._id}})
}

 })

