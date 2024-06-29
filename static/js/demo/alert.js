$(document).ready(function() {
    url = '/system-alerts'
    table = $('#alertDataTable').DataTable({
            retrieve: true,
            sort: true,
           // scrollY: 400,
            ajax: {
                'url': url
            },
          columns: [
            { data: 'stock' },
            {
                data: 'triggerType',
                render: function (data, type) {
                    if (data === 'GT_TRIGGER_PRICE') {
                        return '> than the trigger price';
                    }
                    if (data === 'LT_TRIGGER_PRICE') {
                        return '< than the trigger price';
                    }
                    return '= to the trigger price';
                }
            },
            { data: 'triggerPrice' },
            {
                data: 'dateTime',
                render: function (data, type, row, meta) {
                    return moment.unix(data).format('DD/MM/YYYY h:mm');
                }
            },
            {
                data: 'key',
                render: function (data, type, row, meta) {
                    return '<form action="/deleteRule" method="post"><input type="hidden" value="'+data+'" name="ruleId"><button class="btn btn-danger btn-circle btn-sm" onclick="document.submit();"><i class="fas fa-trash"></i></button></form>';
                }
            }
          ]
    });

});

$.extend( $.fn.dataTable.defaults, {
    searching: false,
    ordering:  true
});
