import jaydebeapi as JDBC
import psycopg2
import psycopg2.extras
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import jpype
import logging
# Create your views here.

def get_jdbc_connection(iotdbIp , iotdbUser , iotdbPassword):

        if jpype.isJVMStarted() and not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()
            jpype.java.lang.Thread.currentThread().setContextClassLoader(jpype.java.lang.ClassLoader.getSystemClassLoader())
        connection = JDBC.connect('org.apache.iotdb.jdbc.IoTDBDriver', iotdbIp, [iotdbUser, iotdbPassword],
					 'iotdb-jdbc-0.9.0-SNAPSHOT-jar-with-dependencies.jar')

        return connection
def Query(request):
	from configparser import ConfigParser
	import os
	conn = ConfigParser()

	file_path = os.path.join(os.path.abspath('.'), 'config.ini')
	if not os.path.exists(file_path):
		raise FileNotFoundError("文件不存在")

	conn.read(file_path)
	pghost = conn.get('api', 'pghost')
	pgport = conn.get('api' , 'pgport')
	pguser = conn.get('api', 'pguser')
	pgpassword = conn.get('api', 'pgpassword')
	pgdatabase = conn.get('api', 'pgdatabase')
	iotdbIp = conn.get('api', 'iotdbIp')
	iotdbUser = conn.get('api', 'iotdbUser')
	iotdbPassword = conn.get('api', 'iotdbPassword')

	print(request.body)
	body = json.loads(str(request.body, encoding = 'utf8'))
	if not body['railLineOid']:
		print('No railLineOid!')
		return JsonResponse({'state':'Error', 'value':'没有选择线路！'})
	roid = body['railLineOid']
		
	if not body['carList']:
		print('No carList!')
		return JsonResponse({'state':'Error', 'value':'没有选择列车！'})
	carList = body['carList']
		
	if not body['terminalList']:
		print('No terminalList!')
		return JsonResponse({'state':'Error', 'value':'没有选择终端！'})
	tmp = body['terminalList'].split(',')
	terminalList = []
	for i in tmp:
		if i == '车头':
			terminalList.append('Head')
		elif i == '车尾':
			terminalList.append('Tail')
	
	if not body['CarriageList']:
		print('No CarriageList!')
		return JsonResponse({'state':'Error', 'value':'没有选择车厢！'})
	carriageList = body['CarriageList'].split(',')
	
	if not body['paraList']:
		print('No paraList!')
		return JsonResponse({'state':'Error', 'value':'没有选择工况！'})
	paraList = body['paraList']
	
	if not body['startTime']:
		print('No startTime!')
		return JsonResponse({'state':'Error', 'value':'没有选择开始时间！'})
	startTime = body['startTime'].split('.')[0]
	
	if not body['endTime']:
		print('No endTime!')
		return JsonResponse({'state':'Error', 'value':'没有选择结束时间！'})
	endTime = body['endTime'].split('.')[0]
	
	if startTime > endTime:
		print('startTime > endTime!')
		return JsonResponse({'state':'Error', 'value':'开始时间晚于结束时间！'})
	
	#iotdb_conn = JDBC.connect('org.apache.iotdb.jdbc.IoTDBDriver', "jdbc:iotdb://192.168.3.31:6667/", ['root', 'root'], 'iotdb-jdbc-0.9.0-SNAPSHOT-jar-with-dependencies.jar')
	iotdb_conn = get_jdbc_connection(iotdbIp , iotdbUser , iotdbPassword)
	iotdb_curs = iotdb_conn.cursor()
	# conn = psycopg2.connect(host = '172.16.50.7', port = 5432, user = 'postgres', password = '123456', database='protodw')
	conn = psycopg2.connect(host=pghost, port=pgport, user=pguser, password=pgpassword, database=pgdatabase)
	cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	sql = "SELECT * FROM plt_tsm_railline WHERE plt_oid = '" + roid + "'"
	cursor.execute(sql)
	qr = cursor.fetchall()
	line_id = qr[0]["plt_lineid"]
	ret = []
	for i in carList:
		for j in terminalList:
			for k in carriageList:
				for l in paraList:
					#time_series = "root." + "BJ8T00" + "." + i + "." + j + ".Carriage" + k
					time_series = "root." + line_id + "." + i + "." + j + ".Carriage" + k
					if l == "OriginalPackage":
						time_series = "root." + line_id + "." + i + "." + j

					#time_series = "root." + "BJ8T00.H411.Head"+".Carriage" + k
					# logging.warning(time_series)
					sql = "SELECT " + l + " FROM " + time_series + " where time >= " + startTime+ " && time <= " + endTime
					#sql = "SELECT " + l + " FROM " + "root.BJ8T00.H411.Head.Carriage2" + " where time <= " + endTime

					# logging.warning(sql)
					try:
						iotdb_curs.execute(sql)
						qr = iotdb_curs.fetchall()
						# print(qr)
						for r in qr:
							ret.append([time_series + "." + l, r[0], r[1]])
					except Exception as e:
						print(e)
	cursor.close()
	conn.close()
	iotdb_curs.close()
	iotdb_conn.close()
	return JsonResponse({'state':'OK', 'value': ret})
