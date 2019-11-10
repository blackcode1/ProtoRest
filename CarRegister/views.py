#coding=utf-8
import jaydebeapi as JDBC
import psycopg2
import psycopg2.extras
import json
from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def Register(request):
	iotdb_conn = JDBC.connect('org.apache.iotdb.jdbc.IoTDBDriver', "jdbc:iotdb://192.168.70.195:6667/", ['root', 'root'], 'iotdb-jdbc-0.8.0-SNAPSHOT-jar-with-dependencies.jar')
	iotdb_curs = iotdb_conn.cursor()
	conn = psycopg2.connect(host = '192.168.70.194', port = 8180, user = 'postgres', password = '123456', database='dataway')
	cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	print(request.POST)
	print(request.body)
	body = json.loads(str(request.body, encoding = 'utf8'))
	if not body['coidList']:
		print('No coidList!')
		iotdb_curs.close()
		iotdb_conn.close()
		cursor.close()
		conn.close()
		return HttpResponse('No coidList!')

	coidList = body['coidList']
	print(coidList)
	roidList = []
	carList = []
	errors = []

	for coid in coidList:
		sql = "SELECT * FROM plt_cus_car WHERE plt_oid = '" + coid + "'"
		cursor.execute(sql)
		car_qr = cursor.fetchall()
		carList.append(car_qr[0])
		if car_qr[0]["plt_railline"] not in roidList:
			roidList.append(car_qr[0]["plt_railline"])

	for roid in roidList:
		sql = "SELECT * FROM plt_tsm_railline WHERE plt_oid = '" + roid + "'"
		cursor.execute(sql)
		qr = cursor.fetchall()
		line_id = qr[0]["plt_lineid"]
	
		sql = "SELECT * FROM plt_tsm_protocol WHERE plt_oid = '" + qr[0]["plt_protoid"] + "'"
		cursor.execute(sql)
		protocol_qr = cursor.fetchall();
	
		work_condition = []
		for protocol in protocol_qr:
			poid = protocol["plt_oid"]
			sql = "SELECT plt_tsm_template.* FROM ((plt_tsm_protocol INNER JOIN	plt_tsm_r_pro2temp ON plt_tsm_protocol.plt_oid = plt_tsm_r_pro2temp.plt_leftoid) INNER JOIN plt_tsm_template ON plt_tsm_r_pro2temp.plt_rightoid = plt_tsm_template.plt_oid) WHERE plt_tsm_protocol.plt_oid = '" + poid + "'"
			cursor.execute(sql)
			template_qr = cursor.fetchall()
			for template in template_qr:
				toid = template["plt_oid"]
				sql = "SELECT plt_tsm_templatepara.* FROM ((plt_tsm_template INNER JOIN plt_tsm_r_tem2tempara ON plt_tsm_template.plt_oid = plt_tsm_r_tem2tempara.plt_leftoid) INNER JOIN plt_tsm_templatepara ON plt_tsm_r_tem2tempara.plt_rightoid = plt_tsm_templatepara.plt_oid) WHERE plt_tsm_template.plt_oid = '" + toid + "'"
				cursor.execute(sql)
				tempara_qr = cursor.fetchall()
				for tempara in tempara_qr:
					if (tempara["plt_paratype"] != "工况参数"):
						continue;
					name = tempara["plt_paraid"]
					type = tempara["plt_datatype"]
					iotdb_type = ""
					if type == "Int":
						iotdb_type = "INT32"
					elif type == "Long":
						iotdb_type = "INT64"
					elif type == "Float":
						iotdb_type = "FLOAT"
					elif type == "Double":
						iotdb_type = "DOUBLE"
					elif type == "String":
						iotdb_type = "TEXT"
					elif type == "Boolean":
						iotdb_type = "BOOLEAN"
					work_condition.append((name, iotdb_type))
	
		for car in carList:
			if (car["plt_railline"] != roid):
				continue
			car_id = car["plt_carid"]
			coid = car["plt_oid"]
			sql = "SELECT * FROM plt_cus_terminal WHERE plt_carid = '" + coid + "'"
			cursor.execute(sql)
			terminal_qr =  cursor.fetchall()
			for terminal in terminal_qr:
				position = terminal["plt_position"]
				terminal_id = terminal["plt_terminalid"]
				if position == "车头":
					terminal_id = "head"
				elif position == "车尾":
					terminal_id = "tail"
				storage_group = "root." + line_id + "." + car_id + "." + terminal_id
				iotdb_sql = "set storage group to " + storage_group
				try:
					iotdb_curs.execute(iotdb_sql)
				except Exception as e:
					if (str(e) != 'java.sql.SQLException: Method not supported'):
						errors.append(str(e))
				try:
					iotdb_sql = "create timeseries " + storage_group + ".OriginalPackage with datatype=TEXT,encoding=PLAIN"
					iotdb_curs.execute(iotdb_sql)
				except Exception as e:
					if (str(e) != 'java.sql.SQLException: Method not supported'):
						errors.append(str(e))
				for i in range(1,7):
					for wc in work_condition:
						try:
							iotdb_sql = "create timeseries " + storage_group + "." + "Carriage" + str(i) + "." + wc[0] + " with datatype=" + wc[1] + ",encoding=PLAIN"
							iotdb_curs.execute(iotdb_sql)
						except Exception as e:
							if (str(e) != 'java.sql.SQLException: Method not supported'):
								errors.append(str(e))
	iotdb_curs.close()
	iotdb_conn.close()
	cursor.close()
	conn.close()
	return HttpResponse(errors)
