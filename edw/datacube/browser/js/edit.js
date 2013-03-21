if(window.scoreboard === undefined){
    var scoreboard = {
        version: '1.0'
    };
};

if(scoreboard.datacube === undefined){
    scoreboard.datacube = {};
};

scoreboard.datacube.edit = {
    renderDatasetsBox: function(){
        var fieldset = jQuery('fieldset#fieldset-default');
        var datasetsBox = jQuery('<div id="datasets-box">');
        fieldset.append(datasetsBox);
        return datasetsBox;
    },
    renderDatasetsBoxLoadButton: function(endpoint, datasetsBox){
        var self = this;
        var fetchDatasetsButton = jQuery('<button>');
        fetchDatasetsButton.text('Fetch datasets');
        fetchDatasetsButton.bind('click', function(evt){
            evt.preventDefault();
            if(!endpoint.val()){
                alert('No endpoint defined!');
            }else{
                self.renderDatasets(endpoint, datasetsBox);
            }
            return false;
        });
        datasetsBox.empty().append(fetchDatasetsButton);
    },
    fetchDatasets: function(endpoint){
        var data = [
            {'uri': 'some-dataset-uri-1',
             'title': 'Some dataset 1'},
            {'uri': 'some-dataset-uri-2',
             'title': 'Some dataset 2'},
            {'uri': 'some-dataset-uri-3',
             'title': 'Some dataset 3'},
            {'uri': 'some-dataset-uri-4',
             'title': 'Some dataset 4'},
            {'uri': 'some-dataset-uri-5',
             'title': 'Some dataset 5'}
        ];
        return data
    },
    renderDatasets: function(endpoint, datasetsBox){
        var self = this;
        var datasetsJSON = self.fetchDatasets(endpoint);
        datasetsBox.empty();
        jQuery.each(datasetsJSON, function(i, o){
            var label = jQuery('<label>');
            label.text(o['title']);
            var field = jQuery('<input type="radio" name="dataset-entry">');
            field.val(o['uri']);
            if(o['uri'] == self.dataset.val()){
                field.attr({'checked': 'checked'});
            }
            label.prepend(field);
            datasetsBox.append(label);
            field.bind('click', function(){
                self.dataset.val(jQuery(this).val());
            });
        })

    },
    registerTriggers: function(){
        var self = this;
        var datasetsBox = self.renderDatasetsBox();
        self.endpoint.bind('keydown', function(){
            if(self.endpoint.val()){
                self.renderDatasetsBoxLoadButton(self.endpoint, datasetsBox);
            }
        });
        self.renderDatasets(self.endpoint, datasetsBox);
    }
};

jQuery(document).ready(function(){
    scoreboard.datacube.edit['endpoint'] = jQuery('textarea[name="endpoint"]');
    scoreboard.datacube.edit['dataset'] = jQuery('input[name="dataset"]');
    scoreboard.datacube.edit.registerTriggers();
});
