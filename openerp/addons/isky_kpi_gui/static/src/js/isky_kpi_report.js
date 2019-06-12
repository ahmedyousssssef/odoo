odoo.define('isky_kpi_gui.isky_kpi_report_tag', function (require)
{
'use strict';

    var ajax = require('web.ajax');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var formats = require('web.formats');
    var session = require('web.session');
    var web_client = require('web.web_client');
    var Widget = require('web.Widget');
    var _t = core._t;
    var QWeb = core.qweb;
    var Model = require('web.Model');

var isky_kpi_report_tag = Widget.extend(ControlPanelMixin,
{

    events:
    {
        "click #emp_kpi": "button_emp_kpi",
        "click #technical_kpi": "button_technical_kpi",
        "click #deadline": "button_deadline",
        "click #appraisal": "button_appraisal"
    },
    button_emp_kpi: function(ev)
    {
        ev.preventDefault();
        this.$searchview.hide();
        this.load_action("isky_kpi_gui.isky_emp_report", {});
    },
    button_technical_kpi: function(ev)
    {
          ev.preventDefault();
          this.load_action("isky_hr_kpi.technical_kpi_action", {});

    },
    button_deadline: function(ev)
    {
        ev.preventDefault();
        this.load_action("isky_hr_kpi.deadline_action", {});

    },
    button_appraisal: function(ev)
    {
        ev.preventDefault();
        this.load_action("isky_hr_kpi.appraisal_action", {});

    },
    init: function(parent)
    {
        this._super(parent);
        this.period = moment().startOf('year').format('YYYY/MM/DD')
        this.period_to = moment().endOf('year').format('YYYY/MM/DD');
        var self = this;
        self.selected_button_id = 'all';
        this.get_total().done(function()
        {
            self.render_report();
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
    get_total: function()
    {
        var self = this;
        return ajax.jsonRpc('/isky_kpi_gui/get_total', 'call',
        {
            date_from: self.period,
            date_to: self.period_to

        }).then(function (result)
        {
            self.total_technical = result.total_technical;
            self.total_deadline = result.total_deadline;
            self.total_appraisal = result.total_appraisal;
            self.technical_share = result.technical_share;
            self.timeline_share = result.timeline_share;
            self.net_technical = result.net_technical;
            self.competencies_evaluation = result.competencies_evaluation;

        });
    },
    render_report_statistics: function()
    {
        var self = this;
        addLoader(this.$('#content_graph'));
        ajax.jsonRpc('/isky_kpi_gui/get_total', 'call',
        {
            date_from: self.period,
            date_to: self.period_to

        }).done(function(result){
            self.$('#content_graph div.o_loader').hide();
            if (self.selected_button_id == 'all')
            {
                var total = result.part1_total + result.part2_total + result.part3_total;
                load_chart('#content_graph',result.part1_total,result.part2_total,result.part3_total,total,result.objectives_arr,result.data_arr);

            }
            else
            {
                console.log('Error');
            }
        });
        function load_chart(div_to_display,part1_total,part2_total,part3_total, result,objectives_arr,data_arr)
        {
            var div_chart = div_to_display.substring(1);
            Highcharts.chart(div_chart,
            {
                title:
                {
                    text: ''
                },
                plotOptions:
                {
                    series:
                    {
                        cursor: 'pointer',
                        point:
                        {
                            events:
                            {
                                click: function (ev)
                                {

                                    location.href = this.series.options.url ;
                                }
                            }
                        }
                    }
                },
                exporting:
                {
                    enabled: false
                },
                xAxis:
                {
                    categories: objectives_arr
                },
                series: data_arr
            });


        }

    },
    render_report: function()
    {
        this.$el.empty().append(QWeb.render("isky_kpi_gui.dashreport",
        {
            total_technical: this.total_technical,
            total_deadline: this.total_deadline,
            total_appraisal: this.total_appraisal,
            technical_share : this.technical_share,
            timeline_share : this.timeline_share,
            net_technical : this.net_technical,
            competencies_evaluation : this.competencies_evaluation


        }));
        this.update_cp();
        this.render_report_statistics();
    },
    on_update_options: function()
    {
        this.period = this.$searchview.find('input[name="period"]').val();
        this.period_to = this.$searchview.find('input[name="period_to"]').val();
        if (this.period > this.period_to)
        {
            alert("Date from must be less than date to.");
        }
        else
        {
            this.get_total();
            this.render_report();
        }
    },
    set_up_datetimepickers: function()
    {
        this.$searchview.find('.datetime_picker').datetimepicker({
            format: 'YYYY/MM/DD',
            viewMode: 'days',
            pickTime: false,
        }).on('dp.change', this.on_update_options);
    },
    update_cp: function()
    {
        this.$searchview = $(QWeb.render("isky_kpi_gui.dashreport_searchview", {
            period: this.period,
            period_to: this.period_to,
        }));

        this.set_up_datetimepickers();
        this.update_control_panel(
        {
            cp_content: {
                $searchview: this.$searchview,
            },
            breadcrumbs: this.getParent().get_breadcrumbs(),
        });
    },


});
function addLoader(selector)
{
    var loader = '<span class="fa fa-3x fa-spin fa-spinner fa-pulse"/>';
    selector.html("<div class='o_loader'>" + loader + "</div>");
}


core.action_registry.add('isky_kpi_report_tag', isky_kpi_report_tag);
});