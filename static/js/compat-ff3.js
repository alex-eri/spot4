
var addEventListener = Element.prototype.addEventListener

Element.prototype.addEventListener = function (sEventType, fListener /*, useCapture (will be ignored!) */) {
return addEventListener.call(this, sEventType, fListener , false)
}

var removeEventListener = Element.prototype.removeEventListener;

Element.prototype.removeEventListener = function (sEventType, fListener /*, useCapture (will be ignored!) */) {
return removeEventListener.call(this, sEventType, fListener, false)
}
