if(window.scoreboard === undefined){
    var scoreboard = {
        version: '1.0'
    };
};

if(scoreboard.datacube === undefined){
    scoreboard.datacube = {};
};

scoreboard.datacube.view = {
    load: function(){
        console.log('DataCube view.js READY!');
    }
};

jQuery(document).ready(function(){
    scoreboard.datacube.view.load();
});
