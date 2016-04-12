#Filter variants according to variables in cutoff.xlsx. This script is called from makeGeminiInput.py
import os
import xlrd
import sys

family = sys.argv[1]
for inheritenceType in ['recessive','dominant','denovo']:
	variantFile='data/' + family + '/' + inheritenceType + 'Unfiltered.txt'
	cutoffFile='data/' + family + '/cutoffs.xlsx'
	filteredFileOut='data/' + family + '/' + inheritenceType + 'Filtered_' + family + '.tsv'

	cutoffs=[]

	#Open cutoffs spreadsheet
	wb = xlrd.open_workbook(cutoffFile)  # xls file to read from
	xl_sheet = wb.sheet_by_index(0) # first sheet in workbook
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
		if len(buildRow)>0 and len(buildRow[0])>0 and buildRow[0][0]!='#':
			buildRow=buildRow[:3]
			cutoffs.append(buildRow)
		

	#Get rows that have variables of interest
	
	with open(variantFile, 'r') as f:
		header = f.readline()
	headerStr=header
	
	write=open(filteredFileOut,'w')
	write.writelines ('#Cutoffs: ')
	


	header=header.strip('\n').split('\t')
	rowsToUse=[]
	cutoffsNew=[]
	okConditionals=['==','!=','>','<','>=','<=']

	
	for cutoff in cutoffs:
		var=cutoff[0]
		pos=0
		rowFound=False
		
		for head in header:
			
			if head==var:
				
				rowsToUse.append(pos)
				rowFound=True
				if cutoff[1] in okConditionals:
					cutoffsNew.append((pos, cutoff[1], cutoff[2]))
				else:
					raise Warning("Cutoff " + var + ' ' +  cutoff[1] + ' ' +  cutoff[2] + ' contains an invalid conditional. Skipping...')
			pos+=1
		if not rowFound:
			raise Warning(' variable ' + var + ' not found in variants - ' + inheritenceType)

	
	
	for cutoff in cutoffs:
		write.writelines(cutoff[0] + cutoff[1] +cutoff[2] + ' ')
	
	write.writelines('\n#'+headerStr)
	cutoffs=cutoffsNew
	def getConditional(var1,var2,conditional):
		try:
			var1=float(var1)
			var2=float(var2)
		except ValueError: pass
		if conditional == '==':
			if var1 == var2:
				ok=True
			else:
				ok=False
		if conditional == '!=':
			if var1 != var2:
				ok=True
			else:
				ok=False
		if conditional == '>=':
			if var1 >= var2:
				ok=True
			else:
				ok=False
		if conditional == '<=':
			if var1 <= var2:
				ok=True
			else:
				ok=False
		if conditional == '>':
			if var1 > var2:
				ok=True
			else:
				ok=False
		if conditional == '<':
			if var1 < var2:
				ok=True
			else:
				ok=False
	
		return ok

	for line in open(variantFile):
	
		if len(line)>2 and line[:5] != 'chrom':
			var=line.strip('\n').split('\t')
		
			allOk=True
			for cutoff in cutoffs:
				ok=getConditional(var[cutoff[0]],cutoff[2],cutoff[1])
				if not ok:
					allOk=False
			if allOk:	
				write.writelines(line)
		

	write.close()		
