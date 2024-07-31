var barCount = 60;
var initialDateStr = '05 Jul 2024 09:14 +0530';

var ctx = document.getElementById('ohlcCanvas').getContext('2d');
ctx.canvas.width = 900;
ctx.canvas.height = 400;

$("#triggerOhlc").click(function(){
    stockVal = getSelectedStock();
    $('#ohlcContainer').modal()

    var date = luxon.DateTime.fromRFC2822(initialDateStr);
    //const time1 = date.toFormat('HH:mm:ss');
    date2 = date.plus({ seconds: 10 });
    date3 = date2.plus({ seconds: 10 });
    date4 = date3.plus({ seconds: 10 });
    date5 = date4.plus({ seconds: 10 });
    date6 = date5.plus({ seconds: 10 });
    date7 = date6.plus({ seconds: 10 });
    date8 = date7.plus({ seconds: 10 });
    date9 = date8.plus({ seconds: 10 });
    date10 = date9.plus({ seconds: 10 });
    date11 = date10.plus({ seconds: 10 });
    temp = [
            {x: date.valueOf(), o: 100, h: 101, l: 99, c: 100},
            {x: date2.valueOf(), o: 100, h: 106, l: 101, c: 105},
            {x: date3.valueOf(), o: 105, h: 106, l: 103, c: 104},
            {x: date4.valueOf(), o:104, h: 112, l: 103, c: 110},
            {x: date5.valueOf(), o: 110, h: 108, l: 109, c: 108},
            {x: date6.valueOf(), o: 108, h: 108, l: 105, c: 106},
            {x: date7.valueOf(), o: 106, h: 114, l: 106, c: 112},
            {x: date8.valueOf(), o: 112, h: 115, l: 109, c: 108},
            {x: date9.valueOf(), o: 108, h: 117, l: 104, c: 110},
           ]
    initial = [{x: date.valueOf(), o: 100, h: 101, l: 99, c: 100},
            {x: date2.valueOf(), o: 100, h: 106, l: 101, c: 105}]
    var chart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [{
                label: stockVal,
                data: initial
            }]
        }
    });

    var socket = new WebSocket('ws://' + location.host + '/ohlc/' + stockVal);
    socket.addEventListener('message', ev => {
        data = JSON.parse(ev.data)
        console.log("*************************************** " +data)
        console.log(data)
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        chart.update();
    });

});

    function getSelectedStock() {
        if ($('#stockHid').val() == '') {
            stockVal = 'HDFCBANK'
        } else {
            stockVal = $('#stockHid').val()
        }
        $('#stockSelector').val(stockVal)
        return stockVal;
    }

//
//var barData = getInitialData(initialDateStr, 50);
//
//var chart = new Chart(ctx, {
//	type: 'candlestick',
//	data: {
//		datasets: [{
//			label: 'Random Curve',
//			data: barData
//		}]
//	}
//});

function getInitialData(dateStr, lastClose) {
    var date = luxon.DateTime.fromRFC2822(dateStr);
    const time = date.toFormat('HH:mm:ss');
	data = [{x: time, o: lastClose, h: lastClose, l: lastClose, c: 100}]
	return data;
}

function randomNumber(min, max) {
	return Math.random() * (max - min) + min;
}

function randomBar(date, lastClose) {
	var open = +randomNumber(lastClose * 0.95, lastClose * 1.05).toFixed(2);
	var close = +randomNumber(open * 0.95, open * 1.05).toFixed(2);
	var high = +randomNumber(Math.max(open, close), Math.max(open, close) * 1.1).toFixed(2);
	var low = +randomNumber(Math.min(open, close) * 0.9, Math.min(open, close)).toFixed(2);
	return {
		x: date.valueOf(),
		o: open,
		h: high,
		l: low,
		c: close
	};

}

function getRandomData(dateStr, count) {
	var date = luxon.DateTime.fromRFC2822(dateStr);
	var data = [randomBar(date, 30)];
	while (data.length < count) {
		date = date.plus({ days: 1 });
		if (date.weekday <= 5) {
			data.push(randomBar(date, data[data.length - 1].c));
		}
	}
	return data;
}

