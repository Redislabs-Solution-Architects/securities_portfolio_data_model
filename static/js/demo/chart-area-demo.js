// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

stockVal = getSelectedStock();
populateMetaData();
displayChart();

$("#stockSelector").change(function(){
    $('#stockForm').submit();
});

function displayChart() {
    // Area Chart Example
    var temp = eval({"price": 0, "timeTrend": 0});
    var socket2 = new WebSocket('ws://' + location.host + '/intraday-trend/' + stockVal);
    var prevTimeStamp = 0;
    var updatePrice = true
    socket2.addEventListener('message', ev => {
        data = JSON.parse(ev.data)
        console.log("***************************************")
        console.log(data)

        for (i in data.timeTrend) {
            myLineChart.data.labels.push(data.timeTrend[i]);
            prevTimeStamp = data.timeTrend[i];
            console.log("Time value: "+data.timeTrend[i]);
        }
       // console.log("updatePrice: "+updatePrice)
        for (i in data.price) {
            myLineChart.data.datasets.forEach((dataset) => {
                console.log("Price value: "+data.price[i]);
                dataset.data.push(data.price[i]);
            });
        }
        myLineChart.update();
    });

    var ctx = document.getElementById("myAreaChart");
    var myLineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: temp.timeTrend,
        datasets: [{
          label: "Price",
          lineTension: 0.1,
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 1,
          pointBackgroundColor: "rgba(78, 115, 223, 1)",
          pointBorderColor: "rgba(78, 115, 223, 1)",
          pointHoverRadius: 1,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 2,
          pointBorderWidth: 1,
          borderWidth: 0.8,
          data: temp.price
        }],
      },
      options: {
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 25,
            top: 25,
            bottom: 0
          }
        },
        scales: {
          xAxes: [{
            time: {
              unit: 'date'
            },
            gridLines: {
              display: false,
              drawBorder: false
            },
            ticks: {
              maxTicksLimit: 10
            }
          }],
          yAxes: [{
            ticks: {
              maxTicksLimit: 6,
              padding: 10,
              callback: function(value, index, values) {
                return number_format(value);
              }
            },
            gridLines: {
              color: "rgb(234, 236, 244)",
              zeroLineColor: "rgb(234, 236, 244)",
              drawBorder: false,
              borderDash: [2],
              zeroLineBorderDash: [2]
            }
          }],
        },
        legend: {
          display: true
        },
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          titleMarginBottom: 10,
          titleFontColor: '#6e707e',
          titleFontSize: 12,
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 5,
          yPadding: 5,
          displayColors: false,
          intersect: false,
          mode: 'index',
          caretPadding: 10,
          callbacks: {
            label: function(tooltipItem, chart) {
              var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
              return datasetLabel + ': $' + number_format(tooltipItem.yLabel);
            }
          }
        }
      }
    });
}

function populateMetaData() {
    const socket = new WebSocket('ws://' + location.host + '/price/' + stockVal);
    socket.addEventListener('message', ev => {
        id="currentPrice"
        data = JSON.parse(ev.data)
        document.getElementById('stockSymbol').innerHTML = data.stockSymbol
        document.getElementById('currentPrice').innerHTML = data.currentPrice
        document.getElementById('minPrice').innerHTML = data.minPrice
        document.getElementById('maxPrice').innerHTML = data.maxPrice
    });
}

function getSelectedStock() {
    if ($('#stockHid').val() == '') {
        stockVal = 'RDBBANK'
    } else {
        stockVal = $('#stockHid').val()
    }
    $('#stockSelector').val(stockVal)
    return stockVal;
}