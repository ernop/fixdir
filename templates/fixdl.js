$(document).ready(function(){
    $("#clearlocks").click(function(){
        $.ajax({
            url:"/clearlocks",
        });
    });
});