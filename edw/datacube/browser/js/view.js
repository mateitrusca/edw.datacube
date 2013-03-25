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
        var target = jQuery('#dataset-dimensions');
        target.empty();
        jQuery.each(data, function(i, o){
            var li = jQuery('<li>');
            var dl = jQuery('<dl>');
            jQuery.each(o, function(label, value){
                var dt = jQuery('<dt>').text(label);
                var dd = jQuery('<dd>').text(value||'null');
                dl.append(dt);
                dl.append(dd);
            });
            li.append(dl);
            target.append(li);
        });
    }
};

jQuery(document).ready(function(){
    scoreboard.datacube.view.getDatasetMetadata();
    scoreboard.datacube.view.getDatasetDimensions();
});
