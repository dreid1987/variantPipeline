import os
import time
from shutil import copyfile
import xlrd
import datetime
import sqlite3 as lite


browseFolders=['/home/david/nksequencer/taskforce/Baylor_Exome_trio_data/ANENCEPHALY/'] #Where data is stored. Inside this folder, have a bunch of folders named for the family. Inside these, have BAM files.
genomeLocation='/home/david/py/database/Homo_sapiens/Ensembl/GRCh37/Sequence/WholeGenomeFasta/genome.fa'


def convertxlsxToPed(fileIn,fileOut):
	individuals=[]
	try:
		#Convert family.xlsx to family.ped
		write=open(fileOut,'w')
		wb = xlrd.open_workbook(fileIn)  # xls file to read from
		xl_sheet = wb.sheet_by_index(0) # first sheet in workbook
		num_cols = xl_sheet.ncols   # Number of columns
		i=0
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
			if i>0:
				write.writelines('\n')
			write.writelines(buildRow[0])
			if buildRow[0][0]!='#':
				individuals.append(buildRow[1])
			for column in buildRow[1:]:
				write.writelines('\t' + column.replace('.0',''))
			i=1
		write.close()
	except IOError: pass
	return individuals
def getPedFile(dataFolder,folder,family,logFile):
	#Convert PED file and get individuals. If there's no PED file, it will try to make one (for trios only).
	ok=False
	individuals=convertxlsxToPed(dataFolder + '/family.xlsx', folder + '/' + family+ '.ped')  #See if PED is in family folder
	if len(individuals)>0:
		pedLocation=folder + '/' +  family + '.ped'
		ok=True
	if len(individuals)==0: #IF no PED...
		individuals=convertxlsxToPed('peds/' + family + '.xlsx', 'peds/' + family + '.ped') #See if PED is in general PED folder
		if len(individuals)>0:
			pedLocation='peds/' + family + '.ped'
			ok=True
	
	if len(individuals)==0: #If no PED yet, try to make PED file
		ok=False

		if numBamFiles==3: #Trios only
			for line in open(folder + '/' +  family + '.vcf'):#find names in VDF file

				if line[:2]=='#C':
	
					individs=line.strip('\n').split('\t')[9:]
	
					#find mother, father, child
					mother=''; father=''; child=''
					for indv in individs:
						if indv.find('1001')>0:
							mother=indv
						if indv.find('1000')>0:
							father=indv
						if indv.find('0001')>0:
							child=indv
					if len(mother)>0 and len(father)>0 and len(child)>0:
						writePed=open(folder + '/' +  family + '.ped','w')
						writePed.writelines('#family_id\tsample_id\tpaternal_id\tmaternal_id\tsex\tphenotype')
						writePed.writelines('\n' + family + '\t' + father + '\t' + '-9' + '\t' + '-9' + '\t' + '1' + '\t' + '1')
						writePed.writelines('\n' + family + '\t' + mother + '\t' + '-9' + '\t' + '-9' + '\t' + '2' + '\t' + '1')
						writePed.writelines('\n' + family + '\t' + child + '\t' + father + '\t' + mother + '\t' + '-9' + '\t' + '2')
						writePed.close()
						ok=True
						writeToLog(logFile,folder + ' PED file generated for default trio: ' + 'data/' + folder + '/' + family+ '.ped')
		
					break
		if not ok:
			writeToLog(logFile,dataFolder + ' - No family.xlsx found and no PED file could be generated')
	
	return pedLocation,ok
def writeToLog(logFile,toWrite):
	r=[]
	if os.path.isfile(logFile):
		f=open(logFile,'r')
		r=f.readlines()
		f.close()
	w=open(logFile,'w')
	for i in r:
		w.writelines(i)
	w.writelines('\n' + toWrite + '\t' + returnTime())
	w.close()

def returnTime():
	
	today=datetime.datetime.today()
	return str(today.year) + '-' + str(today.month) + '-' + str(today.day) + '-' + str(today.hour) + '-' + str(today.minute) + '-' + str(today.second)
logFile='logs/log_' + returnTime()
go=True

def checkPedFile(pedLocation,vcfLocation): #Go through VCF file and get individ IDs. Cross-reference with PED and try to make individ IDs the same.
	
	for line in open(vcfLocation):
		if line[:2] == '#C':
			vcfIndivids=line.strip('\n').split('\t')[9:]
	
	f=open(pedLocation)
	pedString=f.read()
	
	for line in open(pedLocation):
		if line[0]!='#':
			line=line.split('\t')
			individFromPed=line[1]
			
			pedIndividID=individFromPed.split('-')[1]
			
			for vcfIndivid in vcfIndivids:
				vcfIndividID=vcfIndivid.split('-')[1]
				if pedIndividID==vcfIndividID:
					pedString=pedString.replace(individFromPed,vcfIndivid)
	write=open(pedLocation,'w')
	write.writelines(pedString)
	write.close()
	
while go:
	for browseFolder in browseFolders:
		completed=[]
		for line in open('completedRuns.txt'):
			if len(line.strip('\n'))>0:
				completed.append(line.strip('\n'))
	
		folders=os.listdir(browseFolder)
	
		for folder in folders:
			
			if os.path.isdir(browseFolder + folder):
				
				family=folder
				print family
				dataFolder=browseFolder + folder #This is where data and ped files are stored
				folder = 'data/' + folder #This is where working files are generated and stored
				if not os.path.isdir(folder):
					os.mkdir(folder)
			
			
				if family not in completed:
					
					#Scan through all files, make sure not still copying. If still copying, leave this family for now
					for i in ['0','1']:
						vars()['files' + i]=dict()
						for file in os.listdir(dataFolder):
							vars()['files' + i][file] = os.path.getsize(dataFolder + '/' + file)
						time.sleep(2)
					ok=True
					for file in files1.keys():
						try:
							if files1[file] != files0[file]:
								ok=False
						except KeyError: 
							ok=False
					
					if ok:
						writeToLog(logFile,'Analyzing ' + family + '...')
						skipEarly=False
						if os.path.isfile(folder  + '/' +  family  + '.vcf.gz'): #If vcf file is already generated, use that. If you don't want to use the old file, delete it.
							skipEarly=True
							writeToLog(logFile,'Using previous vcf file for ' + family)
						
						if not skipEarly:
							
			
							#Check for BAM files. If no BAM files, check for fastq files and map.
							files = os.listdir(dataFolder)
							bamFiles=""
							numBamFiles=0
							for file in files:

								if file.split('.')[-1] == 'bam':

									if len(bamFiles)>0:
										bamFiles= bamFiles + ' '
									bamFiles = bamFiles + dataFolder + '/' + file
									numBamFiles+=1
							if len(bamFiles)==0:
								#figure out what mapping parameters Baylor uses. Copy those, make BAM from FASTQ
								writeToLog(logFile,dataFolder + ' - No bam files found')
								ok=False
							if len(bamFiles)>0:					
							
								
								#Generate and annotate VCF file
					
								mpileupCommand='samtools mpileup -uf ' + genomeLocation + ' ' + bamFiles  + ' | bcftools view -bvcg - > var.raw.bcf'
								writeToLog(logFile,mpileupCommand)
								os.system(mpileupCommand)	
					
								bcftoolsCommand='bcftools view var.raw.bcf | vcfutils.pl varFilter -D100 > data/' + family + '/' +  family + '.vcf'
						
								writeToLog(logFile,bcftoolsCommand)
								os.system(bcftoolsCommand)
						if ok:	
							#Get PED file
							pedLocation,ok=getPedFile(dataFolder,folder,family,logFile)
							checkPedFile(pedLocation,'data/' +family + '/' + family + '.vcf') #Check if individs in vcf == PED. If not, try to rewrite PED based on VCF individs.
						
						if ok:
							if not skipEarly:
								zlessCommand= 'zless ' + folder  + '/' +  family  + '.vcf | sed s/ID=AD,Number=./ID=AD,Number=R/  | vt decompose -s - | vt normalize -r ' + genomeLocation + ' - | java -Xmx4G -jar snpEff.jar GRCh37.75 -formatEff -classic | bgzip -c > data/' + family + '/' +  family +  '.vcf.gz'
								writeToLog(logFile,zlessCommand)
				
								os.system(zlessCommand)
		
								tabixCommand='tabix -p vcf ' + folder  +  '/' +  family  + '.vcf.gz'
								writeToLog(logFile,tabixCommand)
								os.system(tabixCommand)
		
								#os.remove('data/' + family  + '/' +  family  + '.vcf')
							skipEarly=False
							if os.path.isfile('db/' +  family  + '.db'): #If vcf file is already generated, use that. If you don't want to use the old file, delete it.
								skipEarly=True
								writeToLog(logFile,'Using previous db file for ' + family)
							
							if not skipEarly:
								geminiLoadCommand='gemini load --cores 4 -v ' + folder  + '/' +  family  + '.vcf.gz -t snpEff -p ' + pedLocation + ' db/' + family  + '.db'
	
								writeToLog(logFile,geminiLoadCommand)
								os.system(geminiLoadCommand + ' > tempOut.txt')
								#for line in open('tempOut.txt'):
								#	writeToLog(logFile,line.strip('\n'))
								if not os.path.isfile('db/'+ family  + '.db'):
									ok=False
									writeToLog(logFile,family + ' Gemini load failed - check ped file')
							#Filter variants
							if ok:
								#If no cutoffs.xlsx, add default
								if not os.path.isfile(dataFolder + '/cutoffs.xlsx'):
									copyfile('database/cutoffs.xlsx', 'data/' + family + '/cutoffs.xlsx')
					
								
								os.system('gemini comp_hets db/'+ family  + '.db > data/'+ family  + '/' + 'recessiveUnfiltered.txt')
								os.system('gemini autosomal_dominant db/'+ family  + '.db > data/'+ family  + '/' + 'dominantUnfiltered.txt')
								os.system('gemini de_novo db/'+ family  + '.db > data/'+ family  + '/' + 'denovoUnfiltered.txt')
								os.system('python filterVariants.py ' + family)
							
								#output all annotated variants and add to universal database
	
								writeToLog(logFile,family +' variants outputting to tmp/variants.txt')
								os.system('gemini query -q \"select * from variants\" --header db/' + family + '.db > tmp/variants.txt')
								pos=0
								con = lite.connect('db/all.db')
								cur = con.cursor()  
								for line in open('tmp/variants.txt'):
									if pos==0:
										head=line.strip('\n').split('\t')
										headText='INSERT INTO variants (' + head[0]
			
										for h in head[1:]:
											headText=headText + ',' + h
										headText=headText + ') VALUES ( '
		
									else:
										values=line.strip('\n').split('\t')
										command=headText + '\'' + values[0] + '\''
										for v in values[1:]:
											command = command + ',\'' + v.replace('\'','') + '\''
										command=command + ');'
										cur.execute(command)
									pos=1
								con.commit()	
								con.close()

								os.remove('tmp/variants.txt')

							if ok:
								completed.append(family)
								writeCompleted = open('completedRuns.txt','w')		
								for fam in completed:
									writeCompleted.writelines('\n' + fam)
								writeCompleted.close()
								print family  +' completed'
								writeToLog(logFile,family  + ' completed')
			
	
	time.sleep(100)

