#Looks for new variant filtering and database query requests from users

import os
import time
from shutil import copyfile
import xlrd
import datetime
import sqlite3 as lite
import smtplib
from email.mime.text import MIMEText


variantFilteringInputFolder='variantFilteringInput/'
variantFilteringOutputFolder='variantFilteringOutput/'
databaseQueryInputFolder='databaseQueryInput/'
databaseQueryOutputFolder='databaseQueryOutput/'

def checkFileFinished(file):
	#Check file size to ensure file copy is completed
	fsize1=os.path.getsize(file)
	time.sleep(2)
	fsize2=os.path.getsize(file)
	if fsize1==fsize2:
		return True
	else:
		return False
		
def variantFilteringQuery():
	completed=[]
	for line in open(variantFilteringInputFolder + 'completedRuns.txt'):
		if len(line.strip('\n'))>0:
			completed.append(line.strip('\n'))
	
	files=os.listdir(variantFilteringInputFolder)
	for file in files:
		ok=True
		if file in completed:
			ok=False
		if len(file.split('.'))<1 or file.split('.')[1]!= 'xlsx':
			ok=False
		if ok:
			ok=checkFileFinished(variantFilteringInputFolder + file)
			
		if ok:
			#Open Excel file to get email, family, and inheritence type
			wb = xlrd.open_workbook(variantFilteringInputFolder + file)  # xls file to read from
			xl_sheet = wb.sheet_by_index(0) # first sheet in workbook
			family='';email='';inheritenceType=''
			num_cols = xl_sheet.ncols   # Number of columns
			for row_idx in range(0, xl_sheet.nrows):    # Iterate through rows
				buildRow=[]
				for col_idx in range(0, num_cols):  # Iterate through columns
					cell_obj = xl_sheet.cell(row_idx, col_idx)  # Get cell object by row, col

					try:

						if str(cell_obj)[0]=='t':
							buildRow.append(str(cell_obj).split('\'')[1])
						if str(cell_obj)[0]=='n':
							buildRow.append(str(cell_obj).split(':')[1])
					except IndexError: pass
			
				if len(buildRow)>1:
					if buildRow[0]=='#Email:':
						email=buildRow[1]
					if buildRow[0]=='#Family:':
						family=buildRow[1]
					if buildRow[0]=='#Inheritence type:':
						inheritenceType=buildRow[1]
			print email,family,inheritenceType
			if family=='' or inheritenceType=='':
				ok=False
			if ok:
				os.system('python filterVariants.py ' + family + ' ' + 'data/' + family + '/' + inheritenceType + 'Unfiltered.txt ' + variantFilteringOutputFolder + file.split('.xl')[0] + '_Filtered_' + family + '.tsv ' + variantFilteringInputFolder + file)
				if len(email)>0:
					pass
					#Cannot email on local server... see if Netfriends can help here.
				completed.append(file)
				print file
				writeCompleted = open(variantFilteringInputFolder + 'completedRuns.txt','w')		
				for fam in completed:
					writeCompleted.writelines('\n' + fam)
				
				writeCompleted.close()
def databaseQuery():
	completed=[]
	for line in open(databaseQueryInputFolder + 'completedRuns.txt'):
		if len(line.strip('\n'))>0:
			completed.append(line.strip('\n'))
	
	files=os.listdir(databaseQueryInputFolder)
	for file in files:
		ok=True
		if file in completed:
			ok=False
		if len(file.split('.'))<1 or file.split('.')[1]!= 'xlsx':
			ok=False
		if ok:
			ok=checkFileFinished(databaseQueryInputFolder + file)
			
		if ok:
			#construct database query
			#Open cutoffs spreadsheet
			wb = xlrd.open_workbook(databaseQueryInputFolder + file)  # xls file to read from
			xl_sheet = wb.sheet_by_index(0) # first sheet in workbook
			num_cols = xl_sheet.ncols   # Number of columns
			cutoffs=[]
			for row_idx in range(0, xl_sheet.nrows):    # Iterate through rows
				buildRow=[]
				for col_idx in range(0, num_cols):  # Iterate through columns
					cell_obj = xl_sheet.cell(row_idx, col_idx)  # Get cell object by row, col

					try:
	
						if str(cell_obj)[0]=='t':
							buildRow.append(str(cell_obj).split('\'')[1])
						if str(cell_obj)[0]=='n':
							buildRow.append(str(cell_obj).split(':')[1])
					except IndexError: pass
				if len(buildRow)>0 and len(buildRow[0])>0 and buildRow[0][0]!='#':
					buildRow=buildRow[:3]
					if buildRow[0]!='-':
						cutoffs.append(buildRow)
			command='SELECT * FROM variants WHERE' #Building SQL command
			p=0
			for cutoff in cutoffs:
				if cutoff[1]=='IN':
					command=command + ' ' + cutoff[0] + ' ' + cutoff[1] +  ' ' + '('
					o=0
					for opt in cutoff[2].split(','):
						opt=opt.strip(' ')
						command=command + '\'' + opt + '\''
						o+=1	
						if o<len(cutoff[2].split(',')):
							command = command + ','
					command = command + ')'
				else:
					threshold=cutoff[2]
					try:
						tryFloat=float(threshold)
						if tryFloat==int(tryFloat):
							threshold=str(int(tryFloat))
						command = command + ' ' + cutoff[0] +  ' ' + cutoff[1] +  ' ' +  threshold 
					except ValueError:
						command = command + ' ' + cutoff[0] +  ' ' + cutoff[1] +  ' ' + '\'' + threshold + '\''
				
				p+=1	
				if p<len(cutoffs):
					command = command + ' AND'
				
			command = command
			
			write=open(databaseQueryOutputFolder + file.split('.')[0] + '.tsv','w')
			
			con = lite.connect('db/all.db')
			cur = con.cursor()  
			cur.execute("PRAGMA table_info(variants)")
			data=cur.fetchall()
			pos=0
			for d in data:
				head=d[1]
				if pos>0:
					write.writelines('\t')
				write.writelines(head)
				pos=1
			print command
			#for row in cur.execute(command):
			
			command=command.replace('TABLE','').replace('DROP','')
			for row in cur.execute(command):
				write.writelines('\n')
				p=0
				for d in row:
					if p>0:
						write.writelines('\t')
					
					try:
						write.writelines(str(d))
					except UnicodeEncodeError: pass
					p=1
			con.close()
			write.close()
			
			completed.append(file)
			print file
			writeCompleted = open(databaseQueryInputFolder + 'completedRuns.txt','w')		
			for fam in completed:
				writeCompleted.writelines('\n' + fam)
			
			writeCompleted.close()
			
while True:
	variantFilteringQuery()
	databaseQuery()
	time.sleep(60)
	

