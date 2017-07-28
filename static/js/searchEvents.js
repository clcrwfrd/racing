$(document).ready(function() {
	var offset = $('#numbers li').length;

	$('#numbers').endlessScroll({
		fireOnce: false,
		fireDelay: false,
		loader: '',
		insertAfter: '#numbers li:last',
		content: function(i) {
			return '<li>' + (i + offset) + '</li>';
		}
	});
});