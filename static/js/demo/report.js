
var chart;

$('#stockSelector').change(function() {
    var stockVal = $(this).val();
    var timeframe =  $('#timeframeSelector').val();
    displayChart(timeframe, stockVal)
});


$('#timeframeSelector').change(function() {
    var stockVal = $('#stockSelector').val();
    var timeframe = $(this).val();
    displayChart(timeframe, stockVal)
});

function displayChart(timeframe, stockVal) {
    var ctx = document.getElementById('reportCanvas').getContext('2d');
    if (chart) {
        chart.destroy();
    }
    if (stockVal != '-') {
        chart = new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: stockVal,
                    data: []
                }]
            },
             options: {
                parsing: false,
                spanGaps: true,
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        ticks: {
                            maxTicksLimit: 10
                        },
                        time: {
                            unit: 'day'
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    }
                },
    //            plugins: {
    //                title: {
    //                    display: true,
    //                    text: 'Candlestick Chart Example'
    //                }
    //            }
            }
        });

        url = 'ws://' + location.host + '/report/'+ timeframe + '/' + stockVal
        var socket = new WebSocket(url);

         socket.addEventListener('close', (event) => {
            console.log("Connection closed. Reconnecting...");
            setTimeout(() => {
                console.log("Reconnecting...");
                socket = new WebSocket(url);
                socket.addEventListener('message', ev => {
                    data = JSON.parse(ev.data)

                    price_data = chart.data.datasets[0]
                    for( i in data.price_data){
                        price_data.data.push(data.price_data[i]);
                    }
                    chart.update();
                });
            }, 5000);
        });

        socket.addEventListener('message', ev => {
            data = JSON.parse(ev.data)
            price_data = chart.data.datasets[0]
            for( i in data.price_data){
                price_data.data.push(data.price_data[i]);
            }
//            volume_data = chart.data.datasets[0]
//            for( i in data.volume_data){
//                volume_data.data.push(data.volume_data[i]);
//            }
            chart.update();
        });
    }
}