if(window.scoreboard === undefined){
    var scoreboard = {
        version: '1.0'
    };
};

if(scoreboard.datacube === undefined){
    scoreboard.datacube = {};
};

scoreboard.datacube.view = {
    getDatasetMetadata: function(){
        var self = this;
        jQuery.ajax({
            'url': '@@dataset_metadata',
            'data': {'dataset': jQuery('#dataset-value').text()},
            'success': function(data){
                self.renderDatasetMetadata(data);
            }
        });
    },
    getDatasetDimensions: function(){
        var self = this;
        jQuery.ajax({
            'url': '@@dimensions',
            'success': function(data){
                self.renderDatasetDimensions(data);
            }
        });
    },
    renderDatasetMetadata: function(data){
        var target = jQuery('#dataset-metadata');
        target.empty();
        jQuery.each(data, function(label, value){
            var dt = jQuery('<dt>').text(label);
            var dd = jQuery('<dd>').text(value);
            target.append(dt);
            target.append(dd);
        });
    },
    renderDatasetDimensions: function(data){
        var self = this;
        var target = null;
        jQuery.each(data, function(type, entries){
            if(type == 'dimension' || type == 'group_dimension'){
                target = jQuery('#dataset-dimensions tbody').empty();
            };
            if(type == 'attribute'){
                target = jQuery('#dataset-attributes tbody').empty();
            };
            if(type == 'measure'){
                target = jQuery('#dataset-measures tbody').empty();
            };
            jQuery.each(entries, function(i, o){
                self.renderData(target, o);
            });
        });
    },
    renderData: function(target, data){
        var self = this;
        var tr = jQuery('<tr>');
        self.labelCells(tr, ['notation', 'label', 'comment']);
        self.addDataToTarget(tr, data);
        target.append(tr);
    },
    labelCells: function(tr, order){
        jQuery.each(['notation', 'label', 'comment'], function(i, o){
            var td = jQuery('<td>');
            td.addClass(o);
            tr.append(td);
        });
    },
    addDataToTarget: function(target, data){
        jQuery.each(data, function(name, value){
            var td = jQuery('td.' + name, target);
            if(value){
                td.text(value);
            }else {
                td.text('None');
            }
        });
    },
};

jQuery(document).ready(function(){
    scoreboard.datacube.view.getDatasetMetadata();
    scoreboard.datacube.view.getDatasetDimensions();
});
