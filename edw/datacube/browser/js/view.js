if(window.scoreboard === undefined){
    var scoreboard = {
        version: '1.0'
    };
}

if(scoreboard.datacube === undefined){
    scoreboard.datacube = {};
}

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
    replaceURLWithHTMLLinks: function(text) {
        var exp = /(\b(https?|ftp|file):\/\/[\-A-Z0-9+&@#\/%?=~_|!:,.;]*[\-A-Z0-9+&@#\/%=~_|])/ig;
        return text.replace(exp,"<a href='$1'>$1</a>");
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
        var self = this;
        var target = jQuery('#dataset-metadata');
        target.empty();
        jQuery.each(data, function(label, value){
            var dt = jQuery('<dt>').html(self.replaceURLWithHTMLLinks(label));
            var dd = jQuery('<dd>').html(self.replaceURLWithHTMLLinks(value));
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
            }
            if(type == 'attribute'){
                target = jQuery('#dataset-attributes tbody').empty();
            }
            if(type == 'measure'){
                target = jQuery('#dataset-measures tbody').empty();
            }
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
        var self = this;
        jQuery.each(data, function(name, value){
            var td = jQuery('td.' + name, target);
            if(value){
                td.html(self.replaceURLWithHTMLLinks(value));
            }else {
                td.text('None');
            }
        });
    },
    addNavigation: function(){
      var navigation = new Scoreboard.Views.DatasetNavigationView({
          el: jQuery('#dataset-navigation'),
          cube_url: window.location.href,
          selected_url: window.location.href
      });
    }
};

jQuery(document).ready(function(){
    scoreboard.datacube.view.getDatasetMetadata();
    scoreboard.datacube.view.getDatasetDimensions();
    scoreboard.datacube.view.addNavigation();
});
