function http(i) {
	var row = document.getElementById("row_" + i);
	var childs = row.children;
	
	$.ajax({
		type: "POST",
		url: "/control?action=launch_http&param2=" + childs[1].innerHTML,
		success: function(data) {
			if (data != "failed") {
				$("#label_"+i).text('200 OK');
				$("#http_btn_"+i).remove();
				childs[3].children[0].disabled = true;
			} else {
				$("#label_"+i).text('Failed');
			}
		}
	});
}

function httpAll() {
	var table = document.getElementById("ue_table");
	var rows = table.rows;
	var no_of_rows = rows.length;
	
	for(i = 1; i < no_of_rows-1; i++) {	
		if (rows[i].cells[2].innerHTML == "Attached") {
			http(rows[i].cells[0].innerHTML);
		}
	}
}

function attach(i) {
	var row = document.getElementById("row_" + i);
	var childs = row.children;
	
	$.ajax({
		type: "POST",
		url: "/control?action=launch_ue&param2=" + childs[0].innerHTML,
		success: function(data) {
			if (data != "failed") {
				childs[1].innerHTML = data;
				childs[2].innerHTML = "Attached";
				childs[3].children[0].disabled = false;	
				//document.getElementById("http_" + childs[0].innerHTML);
			} else {
				childs[1].innerHTML = data;
			}
		}
	});
}

function attachAll() {
	var table = document.getElementById("ue_table");
	var rows = table.rows;
	var no_of_rows = rows.length;

	for (i = 1; i < no_of_rows-1; i++) {
		if (rows[i].cells[2].innerHTML != "Attached") {
			attach(rows[i].cells[0].innerHTML);
		}
	}
}
	
function createUEs () {
	var N = $("#ue_input").val();		
	$("#ue_input").attr("disabled", true);
	$("#ue_button").attr("disabled", true);
	var table = '';
	
	for (i = 0; i < N; i++) {
	
		
		$("#ue_table").append("<tr id=row_" + i + "><td>" + i + "</td><td></td><td><button class=\"btn btn-md btn-primary\" attach_" + i + " onclick=attach(" + i + ")>Attach</button></td> <td><button id=http_btn_" +i+ " class=\"btn btn-md btn-primary\" disabled=true onclick=http("+i+")>Send request</button> <label id=label_"+i+"></label></td></tr>");
	}
	$("#ue_table").append("<tr><td></td><td></td><td><button class=\"btn btn-block btn-primary\" id=attach_all onclick=attachAll()>Attach all</button></td><td><button class=\"btn btn-block btn-primary\" id=send_all onclick=httpAll()>Send all</button></td></tr>");

	$.ajax({
		type: "POST",
		url: "/control?action=create_ue&param2=" + $("#ue_input").val(),
		success: function (data) {					
			if (data == "success") {
				$("#enb_status").html('Started');
				$("#enb_button").attr("disabled", true);
			} else {
				//alert("not started");
			}
		}
	});
}

function launchEnb() {
	$.ajax({
		type: "POST",
		url: "/control?action=launch_enb",
		success: function(data) {
			if (data == "success") {
				$("#enb_status").html('Started');
				$("#enb_button").attr("disabled", true);		
				
				$("#ue_input").attr("disabled", false);
				$("#ue_button").attr("disabled", false);
			} else {
				alert("Failed to start enodeb");
			}
			$("#config_list").attr("disabled", true);
		}
	});
}

function activateEnb () {
	$.ajax({
		type: "POST",
		url: "/control?action=setConfig&name=" + $("#config_list option:selected" ).val(),
		success: function(data) {
			if (data == "success") {
				$("#enb_button").attr("disabled", false);
			} else {
				alert("Failed to set config");
			}
		}
	});
}

function getConfig () {
	$.ajax({
		type: "GET",
		url: "/config?action=getNames",
		success: function(data) {
			if (data != "failed") {
				var json = JSON.parse(data);
				var select = document.getElementById("config_name_list");
				var options = [];
				var default_option = document.createElement('option');
				default_option.text = "Select config";
				default_option.setAttribute ("disabled", "disabled");
				default_option.setAttribute ("selected", "selected");
				options.push (default_option.outerHTML);
				
				var option = document.createElement('option');
	
				for (var i = 0; i < json.length; i++) {
					option.text = option.value = json[i]["name"];
					options.push(option.outerHTML);
				}
				select.insertAdjacentHTML('beforeEnd', options.join('\n'));
			}
		}
	});
}

function getConfigInit () {
	$.ajax({
		type: "GET",
		url: "/config?action=getNames",
		success: function(data) {
			if (data != "failed") {
				var json = JSON.parse(data);
				var select = document.getElementById("config_list");
				var options = [];
				var option = document.createElement('option');
	
				for (var i = 0; i < json.length; i++) {
					option.text = option.value = json[i]["name"];
					options.push(option.outerHTML);
				}
				select.insertAdjacentHTML('beforeEnd', options.join('\n'));
			}
		}
	});
}

function configChange () {
	$.ajax({
		type: "GET",
		url: "/config?action=getByName&name=" + $("#config_name_list option:selected" ).val(),
		success: function(data) {
			if (data != "failed") {
				$("#delete_config_button").attr("disabled", false);
				
				var json = JSON.parse(data);
				
				var form = '';
				document.getElementById("config_details").innerHTML = form;
				
				form += '<form id="config-edit-form">';
				form += '<table id="config_details_table" cellspacing="0">';
				
				form += '<tr>';
				form += '<td class="padding-left-10" width="50%"><b>Name</b></td>';
				form += '<td width="50%">';
				form += '<input class="transparent-background" type="text" name="name" value="' + json["name"] + '" readonly/>';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>MCC</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="mcc" value="' + json["mcc"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>MNC</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="mnc" value="' + json["mnc"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>MME IP</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="mme_ip" value="' + json["mme_ip"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>MME Port</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="mme_port" value="' + json["mme_port"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>Global ENB ID</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="global_enbid" value="' + json["global_enbid"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>ENB Name</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="enb_name" value="' + json["enb_name"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>Supported TAs</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="supported_tas" value="' + json["supported_tas"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>Default PagingDRX</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="default_pagingdrx" value="' + json["default_pagingdrx"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>TAI</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="tai" value="' + json["tai"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>E-UTRAN CGI</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="eutrancgi" value="' + json["eutrancgi"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>Return IP</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="returnIP" value="' + json["returnIP"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>RRC Establishment Cause</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="rrc_estb_cause" value="' + json["rrc_estb_cause"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>APN Name</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="apn_name" value="' + json["apn_name"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '<tr>';
				form += '<td class="padding-left-10"><b>Webserver IP</b></td>';
				form += '<td>';
				form += '<input class="transparent-background" type="text" name="webserver_ip" value="' + json["webserver_ip"] + '" />';
				form += '</td>';
				form += '</tr>';
				
				form += '</table>';
				form += '<button id="update_config_button" class="btn btn-primary right" type="button" onclick="submitConfigChange (\'' + json["name"] + '\');"">Update Configuration</button>';
				form += '</form>';
				document.getElementById("config_details").innerHTML = form;
			}
		}
	});
}

function submitConfigChange (name) {
	$("#config-edit-form").ajaxSubmit({
		url: '/config?action=edit&name=' + name,
		type: 'post',
		success: function (data) {
			var modal = '<div class="modal fade" id="modal_edit_success" role="dialog">';
			modal += '<div class="modal-dialog">';
			modal += '<div class="modal-content">';
			modal += '<div class="modal-header">';
			modal += '<button type="button" class="close" data-dismiss="modal">&times;</button>';
			modal += '<h4 class="modal-title">Status</h4>';
			modal += '</div>';
			modal += '<div class="modal-body">';
			modal += '<p>' + data + '</p>';
			modal += '</div>';
			modal += '<div class="modal-footer">';
			modal += '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			document.getElementById("all_modals").innerHTML = modal;
			$('#modal_edit_success').modal('toggle');
		}
	});
}

function deleteConfig () {
	$.ajax({
		type: "POST",
		url: "/config?action=delete&name=" + $("#config_name_list option:selected" ).val(),
		success: function(data) {
			var empty = '';
			document.getElementById("config_details").innerHTML = empty;
			document.getElementById("config_name_list").innerHTML = empty;
			
			getConfig ();
			
			var modal = '<div class="modal fade" id="modal_delete_success" role="dialog">';
			modal += '<div class="modal-dialog">';
			modal += '<div class="modal-content">';
			modal += '<div class="modal-header">';
			modal += '<button type="button" class="close" data-dismiss="modal">&times;</button>';
			modal += '<h4 class="modal-title">Status</h4>';
			modal += '</div>';
			modal += '<div class="modal-body">';
			modal += '<p>' + data + '</p>';
			modal += '</div>';
			modal += '<div class="modal-footer">';
			modal += '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			document.getElementById("all_modals").innerHTML = modal;
			$('#modal_delete_success').modal('toggle');
		}
	});
}

function addNewConfig () {
	$("#config-add-form").ajaxSubmit({
		url: '/config?action=createNew',
		type: 'post',
		success: function (data) {
			var modal = '<div class="modal fade" id="modal_add_success" role="dialog">';
			modal += '<div class="modal-dialog">';
			modal += '<div class="modal-content">';
			modal += '<div class="modal-header">';
			modal += '<button type="button" class="close" data-dismiss="modal">&times;</button>';
			modal += '<h4 class="modal-title">Status</h4>';
			modal += '</div>';
			modal += '<div class="modal-body">';
			modal += '<p>' + data + '</p>';
			modal += '</div>';
			modal += '<div class="modal-footer">';
			modal += '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			modal += '</div>';
			document.getElementById("all_modals").innerHTML = modal;
			
			var empty = '';
			document.getElementById("config_name_list").innerHTML = empty;
			
			getConfig ();
			$('#modal_add_success').modal('toggle');
		}
	});
}