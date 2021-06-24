var charts=[];

function getImage(chart_id) {
    var a = document.createElement('a');
    a.href = charts['#'+chart_id].toBase64Image();
    a.download = chart_id+'.png';
    a.click();
}

function setBarChart(chart, title) {
    $.ajax({
        url: chart.data("url"),
        success: function (data) {

            var ctx = chart[0].getContext("2d");

            var options = {
                responsive: true,
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                },
                scales:
                    {
                        yAxes: [{
                            ticks:
                                {
                                    beginAtZero: true
                                },
                            stacked: true
                        }],
                        xAxes: [{
                            stacked: true
                        }]
                    }
            }

            charts[chart.selector]=new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: data.datasets
                },
                options: options
            });

        }
    });
}

function setPieChart(chart, title) {
    $.ajax({
        url: chart.data("url"),
        success: function (data) {

            var ctx = chart[0].getContext("2d");

            var options = {
                responsive: true,
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                },
            }
            charts[chart.selector] = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels,
                    datasets: data.datasets
                },
                options: options
            });

        }
    });
}
