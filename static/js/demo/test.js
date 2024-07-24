$("#triggerOhlc").click(function(){

   $('#ohlcContainer').modal()

});

var barCount = 60;
var initialDateStr = '01 Apr 2017 00:00 Z';

var ctx = document.getElementById('ohlcCanvas').getContext('2d');
ctx.canvas.width = 800;
ctx.canvas.height = 400;

var barData = getRandomData(initialDateStr, barCount);
function lineData() { return barData.map(d => { return { x: d.x, y: d.c } }) };

var chart = new Chart(ctx, {
	type: 'candlestick',
	data: {
		datasets: [{
			label: 'Random Curve',
			data: barData
		}]
	}
});

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

var update = function () {
	var mixed = document.getElementById('mixed').value;
	var closePrice = {
		label: 'Close Price',
		type: 'line',
		data: null
	};
	// put data in chart
	if (mixed === 'true') {
		closePrice = {
			label: 'Close Price',
			type: 'line',
			data: lineData()
		};
	} else {

	}
	chart.config.data.datasets = [
		{
			label: 'Random Curve',
			data: barData
		},
		closePrice
	]
	chart.update();
};

document.getElementById('update').addEventListener('click', update);

document.getElementById('randomizeData').addEventListener('click', function () {
	barData = getRandomData(initialDateStr, barCount);
	update();
});

