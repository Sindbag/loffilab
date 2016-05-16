function get_resized() {
	$(".img-res-4by3").each(function (index) {
		var that = $(this);
		if (that.width() / 4 >= that.height() / 3) {
			that.css('height', '100%');
			that.width('auto');
		} else {
			that.css('width', '100%');
			that.height('auto');
		}
		that.show();
	});

	$(".img-res-16by9").each(function (index) {
		var that = $(this);
		//console.log(that.width() + " " + that.height() + "\n" + that.width()/16 + " " + that.height()/9);
		if ((that.width() / 16) >= (that.height() / 9)) {
			that.height('100%');
			that.width('auto');
		} else {
			that.width('100%');
			that.height('auto');
		}
		that.show();
	});
}

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
	beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
			xhr.setRequestHeader("X-CSRFToken", csrftoken);
		}
	}
});

$(function () {
	var tmp = false;
	$( '.img-res-4by3 , .img-res-16by9' ).load( function () {
		get_resized();
		tmp = true;
	});
	if (!tmp) {
		get_resized();
		tmp = true;
	}
});

function ajax_fail(xhr, textStatus, errorThrown) {
	$('body').prepend("\
		<div class=\"alert alert-danger noselect\" style=\"position: absolute; right:0; width: 200px; z-index:12500; margin:2rem;\">\
			<a class=\"close\" data-dismiss=\"alert\" aria-label=\"close\">&times;</a>\
			<strong>Произошла какая-то ошибка!</strong>\
		</div>\
	");
	$(".alert").fadeTo(2000, 500).slideUp(500, function(){
		$(".alert").alert('close');
	});
	console.log(xhr.status);
	console.log(textStatus);
	console.log(errorThrown);
}
