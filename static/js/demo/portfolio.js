$(document).ready(function() {
  $('#accDetailDiv').hide()
  document.getElementById('totalSecurityCount').innerHTML = ''
  document.getElementById('totalSecurityCountByTime').innerHTML = ''
  document.getElementById('avgCostPriceByTime').innerHTML = ''
  document.getElementById('portfolioValue').innerHTML = ''

  $("#resultBtnId").click(function() {
    $('#dataTable').DataTable().destroy()
    $('#accDetailDiv').hide()

    account = $.trim($('#accountId').val())
    stock = $.trim($('#stockId').val())
    url = '/transactions?'
    if(account != '' && account != 'undefined'){
      url = url + 'account='+account+'&'
    }
    if(stock != '' && stock != 'undefined'){
      url = url + 'stock='+stock
    }

    table = $('#dataTable').DataTable({
        retrieve: true,
        sort: true,
       // scrollY: 400,
        ajax: {
            'url': url
        },
      columns: [
        { data: 'accountNo' },
       // { data: 'accHolderName' },
        { data: 'ticker' },
        { data: 'date', render: function (data, type, row, meta) {
                return moment.unix(data).format('DD/MM/YYYY h:mm');
            }},
        { data: 'price', render: function (data, type, row, meta) {
                return Number(data/100).toFixed(2);
            }},
        { data: 'quantity' },
        { data: 'lotValue', render: function (data, type, row, meta) {
                return Number(data/100).toFixed(2);
            }}
      ]
    });

   if(account != '' && account != 'undefined'){
      $('#accDetailDiv').show()
      $.ajax({
          url : "/accountstats?account="+account,
          success: function(response){
            res = $.parseJSON(response)
            console.log(res);
            totalSecurityCount = res['totalSecurityCount']
            totalSecurityCountByTime = res['totalSecurityCountByTime']
            avgCostPriceByTime = res['avgCostPriceByTime']
            portfolioValue = res['portfolioValue']

            document.getElementById('totalSecurityCount').innerHTML = totalSecurityCount
            document.getElementById('totalSecurityCountByTime').innerHTML = totalSecurityCountByTime
            document.getElementById('avgCostPriceByTime').innerHTML = avgCostPriceByTime
            document.getElementById('portfolioValue').innerHTML = portfolioValue

          },
          error: function(error){
            console.log(error);
          }
      });
    }

 });

  
});

$.extend( $.fn.dataTable.defaults, {
    searching: false,
    ordering:  false
});
