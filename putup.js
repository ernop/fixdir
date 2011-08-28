function getParameterByName(name)
{
  name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
  var regexS = "[\\?&]" + name + "=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if(results == null)
    return "";
  else
    return decodeURIComponent(results[1].replace(/\+/g, " "));
}

function isScrolledIntoView(elem)
{
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();

    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();

    return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
      && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
}

(function(){
    var img=getParameterByName('img');
    if (img){
        img=parseInt(img);
    }
    if (!img){
        img=1;}
    
    function mkimg(img){
        imgdiv='<div class="image"><img src="images/'+img.toString()+'.jpg"><img src="images/'+img.toString()+'.gif"><img src="images/'+img.toString()+'.png"></div>'
        return imgdiv;
    }
        
    function next(){
        console.log('doing next.');
        $(".status").append('img.'+img);
        $(".contents").append(mkimg(img));
        img=img+1;
    }
    $(document).ready(function(){
        $("#next").click(function(){
            next();
        });
    });
    
    function check(){
        //if end is on screen load more.
        var end=$("#end");
        if (isScrolledIntoView(end)){
            next();
        }
    }
    
    setInterval(check, 200);
})()