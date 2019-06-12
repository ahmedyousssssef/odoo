odoo.define('isky_kpi_gui.emp_report_tag', function (require)
{
'use strict';

    var ajax = require('web.ajax');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var formats = require('web.formats');
    var session = require('web.session');
    var utils = require('web.utils');
    var web_client = require('web.web_client');
    var Widget = require('web.Widget');
    var _t = core._t;
    var QWeb = core.qweb;
    var Model = require('web.Model');

var emp_report_tag = Widget.extend(ControlPanelMixin,
{
    events:
    {
        'change .employees_select': 'onEmpSelected',
        'click #subdornate': 'button_subdornate',
//        'click #tasks': 'button_tasks',
        'click #final': 'button_final',
    },
//    button_tasks: function(ev)
//    {
////        $('.hr_kpi').css('visibility','hidden');
//        var emp_name = $('select[name=employees]').val();
//        var emp_id = $("#employees").children(":selected").attr("id");
//        this.load_tasks(emp_name,emp_id).then((result) =>
//        {
//            $(".hr_kpi" ).empty();
//            Highcharts.chart('content_graph2',
//            {
//                chart:
//                {
//                    type: 'column'
//                },
//                title:
//                {
//                    text: 'Tasks Analysis of: '+emp_name
//                },
//                exporting:
//                {
//                    enabled: false
//                },
//                xAxis:
//                {
//                    categories: ['Task1','Task2','Task3']
//                },
//                yAxis: [
//                {
//                    min: 0,
//                    title:
//                    {
//                        text: 'Employees'
//                    }
//                },
//                {
//                    title:
//                    {
//                        text: 'Weight'
//                    },
//                    opposite: true
//                }],
//                legend:
//                {
//                    shadow: false
//                },
//                tooltip:
//                {
//                    shared: true
//                },
//                plotOptions:
//                {
//                    column:
//                    {
//                        grouping: false,
//                        shadow: false,
//                        borderWidth: 0
//                    }
//                },
//                series: [
//                {
//                    name: 'Technical Weight',
//                    color: 'rgba(165,170,217,1)',
//                    data: [150, 73, 20],
//                    pointPadding: 0.3,
//                    pointPlacement: -0.2
//                },
//                {
//                    name: 'Task Weight(KPI)',
//                    color: 'rgba(126,86,134,.9)',
//                    data: [140, 90,40],
//                    pointPadding: 0.4,
//                    pointPlacement: -0.2
//                },
//                {
//                    name: 'Deadline Weight',
//                    color: 'rgba(248,161,63,1)',
//                    data: [183.6, 178.8, 198.5],
//                    pointPadding: 0.3,
//                    pointPlacement: 0.2,
//                    yAxis: 1
//                },
//                {
//                    name: 'Task Weight(Deadline)',
//                    color: 'rgba(186,60,61,.9)',
//                    data: [203.6, 198.8, 208.5],
//                    pointPadding: 0.4,
//                    pointPlacement: 0.2,
//                    yAxis: 1
//                }]
//            });
//            $(".hr_kpi").append('<center><h1> NO.Tasks: <font style="color:red;">'+result.no_tasks+'</font></h></center>');
//        });
//    },
    button_subdornate:function(ev)
    {
        var emp_name = $('select[name=employees]').val();
        var emp_id = $("#employees").children(":selected").attr("id");
        this.load_data(emp_name,emp_id).then((result) =>
        {

            $("#content_graph2" ).empty();
            $("#content_graph2").append('<center><div><span><font style="color: red;font-size: 35px;">Supervisory role </font> <div style="width: 68%;margin-top: 40px;!important">'+result.subordinates_text+'</span></div></div></center>');
        });

    },
    button_final:function(ev)
    {
        var emp_name = $('select[name=employees]').val();
        var emp_id = $("#employees").children(":selected").attr("id");
        this.load_data(emp_name,emp_id).then((result) =>
        {

            $("#content_graph2" ).empty();
            $("#content_graph2").append('<center>'+result.competencies_appraisal+'</center>');
            $("#content_graph2").append('<center><div style="width: 68%;!important">'+result.employee_self_performance_appraisal+'</div></center>');
        });

    },
    load_action: function(view_xmlid, options)
    {
        options.on_reverse_breadcrumb = this.on_reverse_breadcrumb;
        var self = this;
        new Model("ir.model.data")
        .call("xmlid_to_res_id", [view_xmlid])
        .then(function(data)
         {
            self.do_action(data, options).then(function()
            {
                if (options.push_main_state && self.main_dashboard_action_id)
                {
                    web_client.do_push_state({action: self.main_dashboard_action_id});
                }
            });
        });
    },
    onEmpSelected: function(ev)
    {
        this.load_data(ev.target.value,ev.target.selectedOptions[0].id).then((result) =>
        {
            $('.hr_kpi').css('visibility','visible');
            load_chart('#content_graph2',result.tasks_arr,result.technical_kpi_arr,result.deadline_arr);
            function load_chart(div_to_display,tasks_arr,technical_kpi_arr,deadline_arr)
            {
                var div_chart = div_to_display.substring(1);
                Highcharts.chart(div_chart,
                {
                    chart:
                    {
                        type: 'line'
                    },
                    title:
                    {
                        text: ''
                    },
                    subtitle:
                    {
                        text: ''
                    },
                    exporting:
                    {
                        enabled: false
                    },
                    xAxis:
                    {
                        categories: tasks_arr
                    },
                    yAxis:
                    {
                        title:
                        {
                            text: 'Score'
                        }
                    },
                    plotOptions:
                    {
                        line:
                        {
                            dataLabels:
                            {
                                enabled: true
                            },
                            enableMouseTracking: false
                        }
                    },
                    series: [
                    {
                        name: 'Technical KPI',
                        data: technical_kpi_arr
                    },
                    {
                        name: 'Deadline',
                        data: deadline_arr
                    }]
                });
            }
        });

    },
    init: function(parent)
    {
        this._super(parent);
        this.selected_button_id = 'all';
        var self = this;
        self.render_report();
    },

    load_employees: function ()
    {
        return ajax.jsonRpc('/isky_kpi_gui/get_all_emps', 'call');
    },
    load_data: function (empName,empId)
    {
        return ajax.jsonRpc('/isky_kpi_gui/get_date_for_each_employee', 'call',
        {
            emp_name: empName,
            emp_id : empId
        });
    },
    load_tasks: function (empName,empId)
    {
        return ajax.jsonRpc('/isky_kpi_gui/get_tasks_for_each_employee', 'call',
        {
            emp_name: empName,
            emp_id : empId
        });
    },

    render_report: function()
    {

        this.load_employees().then((response) =>
        {
            this.$el.empty().append(QWeb.render("isky_kpi_gui.dash",
            {
                    employees: response.employees
            }));
        });

    },


});
core.action_registry.add('emp_report_tag', emp_report_tag);
});