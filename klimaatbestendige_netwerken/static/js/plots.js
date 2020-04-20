$('#countingpoint').on('change',function(){

    $.ajax({
        url: "/update_graph",
        type: "GET",
        contentType: 'application/json;charset=UTF-8',
        data: {
            'selected': document.getElementById('countingpoint').value
        },
        dataType:"json",
        success: function (graph) {
            Plotly.newPlot('graph', graph );
        }
    });
})
