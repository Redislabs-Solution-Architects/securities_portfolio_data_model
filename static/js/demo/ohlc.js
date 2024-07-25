var barCount = 60;
var initialDateStr = '05 Jul 2024 09:14 +0530';

var ctx = document.getElementById('ohlcCanvas').getContext('2d');
ctx.canvas.width = 900;
ctx.canvas.height = 500;

$("#triggerOhlc").click(function(){
    stockVal = getSelectedStock();
    $('#ohlcContainer').modal()
    var date = luxon.DateTime.fromRFC2822(initialDateStr);
    date2 = date.plus({ seconds: 10 });
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
