#coding=utf-8
import psycopg2
import psycopg2.extras
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.http import HttpResponse
import os

#输出XML添加缩进
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
			
#为XML某个节点下添加一组查询结果
def addContent(elem, content):
	a = True
	for i in content.keys():
		tmp = ET.SubElement(elem, i)
		if content[i] is not None:
			if type(content[i]) != type(a):
				text = str(content[i])
				tmp.text = text.strip()
			elif content[i]:
				tmp.text = 'true'
			else:
				tmp.text = 'false'
			
# Create your views here.
def XMLexport(request):
	'''print(request.POST)
	if not request.POST.get('pOidList'):
		print('No poidList!')
		return 'No pOidList!'

	poidList = request.POST.get('pOidList')
	print(poidList)
	'''
	print(request.GET)
	if not request.GET.get('poidList'):
		print('No poidList!')
		return HttpResponse('No poidList!')

	poidList = [request.GET.get('poidList')]
	print(poidList)

	#ElementTree 构建XML元素框架
	protName = ""
	protocol = ET.Element('protocol')
	tree = ET.ElementTree(protocol)
	protList = ET.SubElement(protocol, 'protList')
	protSolnList = ET.SubElement(protocol, 'protSolnList')
	templtList = ET.SubElement(protocol, 'templtList')
	tmpSolnList = ET.SubElement(protocol, 'tmpSolnList')
	paraList = ET.SubElement(protocol, 'paraList')
	paraSolnList = ET.SubElement(protocol, 'paraSolnList')
	canIDList = ET.SubElement(protocol, 'canIDList')

	#psycopg2数据库连接 To-Do: 改为从配置文件读取
	conn = psycopg2.connect(host = '192.168.70.194', port = 8180, user = 'postgres', password = '123456', database='dataway')
	cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	#协议处理方案集合
	ptsOidSet = set([])

	for poid in poidList:
		tpQue = []
		#查询协议
		sql = "SELECT * FROM plt_tsm_protocol WHERE plt_oid = '" + poid + "'"
		cursor.execute(sql)
		qr = cursor.fetchall()
		if (len(qr) >= 1):
			protName = qr[0]["plt_protname"]
			prot = ET.SubElement(protList, 'prot')
			addContent(prot, qr[0])
			#查询协议处理方案，去重
			sql = "SELECT * FROM plt_tsm_protreatclass WHERE plt_oid = '" + qr[0]["plt_treatclass"] + "'";
			cursor.execute(sql)
			qr = cursor.fetchall()
			if (len(qr) >= 1):
				psOid = qr[0]['plt_oid']
				#判断是否重复
				if (psOid not in ptsOidSet):
					protSoln = ET.SubElement(protSolnList, 'protSoln')
					addContent(protSoln, qr[0])
					ptsOidSet.add(psOid)
			
			tempOidList = ET.SubElement(prot, 'tempOidList')
			#查询写入协议关联的模版的oid到协议标签下，写入模版信息到templtList
			sql = "SELECT plt_tsm_template.* FROM ((plt_tsm_protocol INNER JOIN	plt_tsm_r_pro2temp ON plt_tsm_protocol.plt_oid = plt_tsm_r_pro2temp.plt_leftoid) INNER JOIN plt_tsm_template ON plt_tsm_r_pro2temp.plt_rightoid = plt_tsm_template.plt_oid) WHERE plt_tsm_protocol.plt_oid = '" + poid + "'"
			cursor.execute(sql)
			qr = cursor.fetchall()
			#每个循环处理一个模版
			#模板参数集合
			pOidSet = set([])
			psOidSet = set([])
			tOidSet = set([])
			tsOidSet = set([])
			sql = "SELECT plt_tsm_templatepara.* FROM ((plt_tsm_protocol INNER JOIN	plt_tsm_r_pro2para ON plt_tsm_protocol.plt_oid = plt_tsm_r_pro2para.plt_leftoid) INNER JOIN plt_tsm_templatepara ON plt_tsm_r_pro2para.plt_rightoid = plt_tsm_templatepara.plt_oid) WHERE plt_tsm_protocol.plt_oid = '" + poid + "'"
			cursor.execute(sql)
			poro_head_qr = cursor.fetchall()
			poro_head_oid_list = ET.SubElement(prot, 'paraOidList')
			for i in range(len(poro_head_qr)):
				paraType = str(poro_head_qr[i]['plt_paratype'])
				paraId = str(poro_head_qr[i]['plt_paraid'])
				#1. 把模板参数oid写在模板标签下
				#！！！！改，加一个List，如果该模版参数已经保存过则不再保存, 但是模版参数的oid加入unique的即可
				pOidText = str(poro_head_qr[i]['plt_oid'])
				pOid = ET.SubElement(poro_head_oid_list, 'pOid')
				pOid.text = pOidText
				sql = "SELECT * FROM plt_tsm_r_pro2para WHERE plt_leftoid = '" + poid + "' AND plt_rightoid = '" + pOidText + "'"
				cursor.execute(sql)
				qrR = cursor.fetchall()
				if (len(qrR) >= 1):
					offset = str(qrR[0]['plt_offset'])
					order = str(qrR[0]['plt_order'])
					pOid.set('offset', offset)
					pOid.set('order', order)
				if pOidText not in pOidSet:
					pOidSet.add(pOidText)
					#2. 把对应的模版参数记录写在paraList的para标签下
					para = ET.SubElement(paraList, 'para')
					addContent(para, poro_head_qr[i])
					#把模版参数解决方案写在paraSolnList对应的pSoln对应的标签下
					sql = "SELECT plt_tsm_paratreatclass.* FROM plt_tsm_templatepara INNER JOIN plt_tsm_paratreatclass ON plt_tsm_templatepara.plt_treatclass = plt_tsm_paratreatclass.plt_oid WHERE plt_tsm_templatepara.plt_oid = '" + pOidText + "'";
					cursor.execute(sql)
					pSolnQr = cursor.fetchall()
					#3. 模板参数解决方案oid写入para的solnOid标签下
					#注意：模版参数解决方案可能为空
					solnOid = ET.SubElement(para, 'solnOid')
					if (len(pSolnQr)>=1):
						pSolnOid = str(pSolnQr[0]['plt_oid'])
						#参数oid
						solnOid.text = pSolnOid
						#参数解决方案的Oid肯定是要写在para里的，但是如果重复不用重复在paraSolution里写
						if (pSolnOid not in psOidSet):
							pSoln = ET.SubElement(paraSolnList, 'pSoln')
							addContent(pSoln, pSolnQr[0])
							psOidSet.add(pSolnOid)
				
			for i in range(len(qr)):
				#1. 模板oid写在协议tempOidList中
				tOid = ET.SubElement(tempOidList, 'tOid')
				tOidText = qr[i]['plt_oid']
				tOid.text = tOidText
				#2. 每个模板的记录写在templtList下的每个template标签下
				template = ET.SubElement(templtList, 'template')
				addContent(template, qr[i])
				#每个template加paraOidList标签
				paraOidList = ET.SubElement(template, 'paraOidList')
				#查询模版对应的模板参数
				#注意模版的模版参数可能为空
				sql = "SELECT plt_tsm_templatepara.* FROM ((plt_tsm_template INNER JOIN plt_tsm_r_tem2tempara ON plt_tsm_template.plt_oid = plt_tsm_r_tem2tempara.plt_leftoid) INNER JOIN plt_tsm_templatepara ON plt_tsm_r_tem2tempara.plt_rightoid = plt_tsm_templatepara.plt_oid) WHERE plt_tsm_template.plt_oid = '" + tOidText + "'"
				cursor.execute(sql)
				tpltParaQr = cursor.fetchall()
				#每次循环处理一个模版参数
				for j in range(len(tpltParaQr)):
					paraType = str(tpltParaQr[j]['plt_paratype'])
					paraId = str(tpltParaQr[j]['plt_paraid'])
					if (paraType == "子模板参数"):
						tpQue.append(paraId)
					#1. 把模板参数oid写在模板标签下
					#！！！！改，加一个List，如果该模版参数已经保存过则不再保存, 但是模版参数的oid加入unique的即可
					pOidText = str(tpltParaQr[j]['plt_oid'])
					pOid = ET.SubElement(paraOidList, 'pOid')
					pOid.text = pOidText
					sql = "SELECT * FROM plt_tsm_r_tem2tempara WHERE plt_leftoid = '" + tOidText + "' AND plt_rightoid = '" + pOidText + "'"
					cursor.execute(sql)
					qrR = cursor.fetchall()
					if (len(qrR) >= 1):
						offset = str(qrR[0]['plt_offset'])
						order = str(qrR[0]['plt_order'])
						pOid.set('offset', offset)
						pOid.set('order', order)
					if pOidText not in pOidSet:
						pOidSet.add(pOidText)
						#2. 把对应的模版参数记录写在paraList的para标签下
						para = ET.SubElement(paraList, 'para')
						addContent(para, tpltParaQr[j])
						#把模版参数解决方案写在paraSolnList对应的pSoln对应的标签下
						sql = "SELECT plt_tsm_paratreatclass.* FROM plt_tsm_templatepara INNER JOIN plt_tsm_paratreatclass ON plt_tsm_templatepara.plt_treatclass = plt_tsm_paratreatclass.plt_oid WHERE plt_tsm_templatepara.plt_oid = '" + pOidText + "'";
						cursor.execute(sql)
						pSolnQr = cursor.fetchall()
						#3. 模板参数解决方案oid写入para的solnOid标签下
						#注意：模版参数解决方案可能为空
						solnOid = ET.SubElement(para, 'solnOid')
						if (len(pSolnQr)>=1):
							pSolnOid = str(pSolnQr[0]['plt_oid'])
							#参数oid
							solnOid.text = pSolnOid
							#参数解决方案的Oid肯定是要写在para里的，但是如果重复不用重复在paraSolution里写
							if (pSolnOid not in psOidSet):
								pSoln = ET.SubElement(paraSolnList, 'pSoln')
								addContent(pSoln, pSolnQr[0])
								psOidSet.add(pSolnOid)
				#3. 把模板对应的解决方案写入tmpSolnList各自的tmpSoln标签下
				sql = "SELECT plt_tsm_temptreclass.* FROM plt_tsm_template INNER JOIN plt_tsm_temptreclass ON plt_tsm_template.plt_treatclass = plt_tsm_temptreclass.plt_oid WHERE plt_tsm_template.plt_oid = '" + tOidText + "'"
				cursor.execute(sql)
				tQr = cursor.fetchall()
				if (len(tQr) >= 1):
					tsOid = str(tQr[0]['plt_oid'])
					if tsOid not in tsOidSet:
						tsOidSet.add(tsOid)
						tmpSoln = ET.SubElement(tmpSolnList, 'tmpSoln')
						addContent(tmpSoln, tQr[0])
						
				sql = "SELECT * FROM plt_tsm_tempid WHERE plt_tempid = '" + tOidText +"'"
				cursor.execute(sql)
				canIDs = cursor.fetchall()
				for canID in canIDs:
					canIDElement = ET.SubElement(canIDList, 'canID')
					addContent(canIDElement, canID)
						
			#子模板
			for stp in tpQue:
				if (stp not in tOidSet):
					tOidSet.add(stp)
					#找到template表中的子模版
					sql = "SELECT * FROM plt_tsm_template WHERE plt_templateid = '" + stp + "'"
					cursor.execute(sql)
					qr = cursor.fetchall()
					if (len(qr) > 0):
						tOidText = qr[0]['plt_oid']
						#每个子模版的记录写在templtList下的每个template标签下
						template = ET.SubElement(templtList, 'template')
						addContent(template, qr[0])
						#每个template加paraOidList标签
						paraOidList = ET.SubElement(template, 'paraOidList')
						#查询模板对应的模板参数
						#注意模板的模板参数可能为空
						sql = "SELECT plt_tsm_templatepara.* FROM ((plt_tsm_template INNER JOIN plt_tsm_r_tem2tempara ON plt_tsm_template.plt_oid = plt_tsm_r_tem2tempara.plt_leftoid) INNER JOIN plt_tsm_templatepara ON plt_tsm_r_tem2tempara.plt_rightoid = plt_tsm_templatepara.plt_oid) WHERE plt_tsm_template.plt_oid = '" + tOidText + "'"
						cursor.execute(sql)
						tpltParaQr = cursor.fetchall()
						#每次循环处理一个模版参数
						for i in range(len(tpltParaQr)):
							paraType = str(tpltParaQr[i]['plt_paratype'])
							paraId = str(tpltParaQr[i]['plt_paraid'])
							if (paraType == "子模板参数"):
								tpQue.append(paraId)
							#1. 把模板参数oid写在模板标签下
							#改，加一个List，如果该模版参数已经保存过则不再保存，但是模板参数的oid加入unique的即可
							pOidText = str(tpltParaQr[i]['plt_oid'])
							pOid = ET.SubElement(paraOidList, 'pOid')
							pOid.text = pOidText
							sql = "SELECT * FROM plt_tsm_r_tem2tempara WHERE plt_leftoid = '" + tOidText + "' AND plt_rightoid = '" + pOidText + "'"
							cursor.execute(sql)
							qrR = cursor.fetchall()
							if (len(qrR) > 0):
								offset = str(qrR[0]['plt_offset'])
								order = str(qrR[0]['plt_order'])
								pOid.set('offset', offset)
								pOid.set('order', order)
							if (pOidText not in pOidSet):
								pOidSet.add(pOidText)
								#2. 把对应的模板参数记录写在paraList的para标签下
								para = ET.SubElement(paraList, 'para')
								addContent(para, tpltParaQr[i])
								#把模板参数解决方案写在paraSolnList对应的pSoln对应的标签下
								sql = "SELECT plt_tsm_paratreatclass.* FROM plt_tsm_templatepara INNER JOIN plt_tsm_paratreatclass ON plt_tsm_templatepara.plt_treatclass = plt_tsm_paratreatclass.plt_oid WHERE plt_tsm_templatepara.plt_oid = '" + pOidText + "'";
								cursor.execute(sql)
								pSolnQr = cursor.fetchall()
								#3. 模板参数解决方案oid写入para的solnOid标签下
								#注意：模版参数解决方案可能为空
								solnOid = ET.SubElement(para, 'solnOid')
								if (len(pSolnQr) > 0):
									pSolnOid = str(pSolnQr[0]['plt_oid'])
									#参数oid
									solnOid.text = pSolnOid
									#参数解决方案的Oid肯定是要写在para里的，但是如果重复不用重复在paraSolution里写
									if (pSolnOid not in psOidSet):
										pSoln = ET.SubElement(paraSolnList, 'pSoln')
										addContent(pSoln, pSolnQr[0])
										#如果oid存在，在hashset中是否可重复
										psOidSet.add(pSolnOid)
						#3. 把子模板对应的解决方案写入tmpSolnList各自的tmpSoln标签下
						sql = "SELECT plt_tsm_temptreclass.* FROM plt_tsm_template INNER JOIN plt_tsm_temptreclass ON plt_tsm_template.plt_treatclass = plt_tsm_temptreclass.plt_oid WHERE plt_tsm_template.plt_oid = '" + tOidText + "'"
						cursor.execute(sql)
						tQr = cursor.fetchall()
						if len(tQr) > 0:
							tsOid = str(tQr[0]['plt_oid'])
							if (tsOid not in tsOidSet):
								tsOidSet.add(tsOid)
								tmpSoln = ET.SubElement(tmpSolnList, 'tmpSoln')
								addContent(tmpSoln, tQr[0])

	
	#写入文件
	if (len(poidList) > 1):
		protName = 'protocol'
	indent(protocol)
	tree.write(protName + '.xml', xml_declaration = True, encoding = 'UTF-8', method = 'xml')
	file=open(protName + '.xml','rb')  
	response = HttpResponse(file)  
	response['Content-Type']='application/octet-stream'  
	response['Content-Disposition']='attachment;filename="' + protName + '.xml"'
	os.remove(protName + '.xml')
	return response 
