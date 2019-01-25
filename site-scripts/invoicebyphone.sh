#!/bin/bash

mongoimport --db spot4 --collection friends --type csv --file $1 
--fields "phone.string()" --drop --columnsHaveTypes

mongo < invoicebyphone.js
