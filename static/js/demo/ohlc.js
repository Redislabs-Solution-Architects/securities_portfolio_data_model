$(document).ready(function() {
    const data = [
            { t: Date.now()+1, o: 100, h: 105, l: 95, c: 102 },
            { t: Date.now()+2, o: 102, h: 110, l: 101, c: 108 },
            { t: Date.now()+3, o: 108, h: 112, l: 107, c: 110 },
            { t: Date.now()+4, o: 110, h: 115, l: 108, c: 112 },
        ];
    displayCandlestickChart()


    function displayCandlestickChart(){
        //var ctx = document.getElementById("ohlcCanvas");
        const ctx = document.getElementById('ohlcCanvas');
        const myChart = new Chart(ctx, {
                type: 'candlestick',
                data: {
                    datasets: [{
                        label: 'Candlestick Chart',
                        data: data
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day'
                            },
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Price'
                            }
                        }
                    }
                }
        });
    }



    $("#triggerOhlc").click(function(){

       $('#ohlcContainer').modal()

    });


});


