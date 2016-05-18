import os
import time
from shutil import copyfile
import xlrd
import datetime
import sqlite3 as lite

readDepthCutoff=4

java7Location='/usr/lib/jvm/jre1.7.0/jre1.7.0_79/bin/java'

#browseFolders=['/home/david/nksequencer/taskforce/Baylor_Exome_trio_data/'] #Where data is stored. Inside this folder, have a bunch of folders named for the family. Inside these, have BAM files. Includ a slash at the end.
#browseFolders=['/home/david/nksequencer/taskforce/Baylor_Exome_trio_data/'] #Where data is stored. Inside this folder, have a bunch of folders named for the family. Inside these, have BAM files. Includ a slash at the end.
browseFolders=['bams/'] #Where data is stored. Inside this folder, have a bunch of folders named for the family. Inside these, have BAM files. Includ a slash at the end.
genomeLocation='/home/david/py/database/Homo_sapiens/Ensembl/GRCh37/Sequence/WholeGenomeFasta/genome.fa'

class mdict(dict):
	def __setitem__(self, key, value):
		 self.setdefault(key, []).append(value)

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
def getPedFile(dataFolder,folder,family,logFile,numBamFiles):
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
			for line in open(folder + '/' +  family + '.vcf'):#find names in VCF file

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
						writeToLog(logFile,'PED file generated for default trio: ' + folder + '/' + family+ '.ped')
						pedLocation=folder + '/' +  family + '.ped'
					break
		if not ok:
			writeToLog(logFile,dataFolder + ' - No family.xlsx found and no PED file could be generated')
			pedLocation=""
	
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
def getCompletedRuns():
	completed=[]
	for line in open('completedRuns.txt'):
		if len(line.strip('\n'))>0:
			completed.append(line.strip('\n'))
	return completed	
def getVersionInfo():
	geminiLoc='~/py/database/GEMINI/'
	geminiConfigFile=geminiLoc + 'data/gemini-config.yaml'
	snpEffSummaryLoc='snpEff_summary.html'
	
	nextLine=''
	for line in open (snpEffSummaryLoc,'r'):
		if nextLine=='version':
			version=line.split('pre')[1][1:-2]
		if nextLine=='genome':
			genome=line.split('td')[1][1:-2]
		if nextLine=='date':
			genome=line.split('td')[1][1:-2]
		if line.find('td valign=top> <b> Genome </b>')>0:
			nextLine='genome'
		elif line.find('td valign=top> <b> Date </b> </td')>0:
			nextLine='date'
		elif line.find('td valign=top> <b> SnpEff version </b> </td')>0:
			nextLine='version'
		else:
			nextLine=''
	

	with open(geminiConfigFile, 'r') as content_file:
		geminiInfo = content_file.read()
	geminiInfo='\n#' + geminInfo.replace('\n','')
	return '#' + date + '\t' + genome + '\t' + version + geminiInfo	
	
def selectVariants(pedFile,vcfFile):
	importantEffects=['SPLICE_SITE_ACCEPTOR','SPLICE_SITE_DONOR','FRAME_SHIFT','NON_SYNONYMOUS_CODING','STOP_GAINED','STOP_LOST','START_LOST','CODON_CHANGE_PLUS_CODON_DELETION','CODON_CHANGE_PLUS_CODON_INSERTION','CODON_CHANGE_PLUS_CODON_INSERTION']
	
	def testRecessive(people,isParent,isAffected,isUnaffected,isMother,inList,codename):
		"""
		Rules:
		Parents are hets
		affecteds are homozygous alternate
		unaffecteds are not homozygous alternate
		"""
		ok=True
		
		for person in isParent:
			if people[person] != 'het':
				ok=False
		if ok:
			for person in isAffected:
				if people[person] != 'homoAlt':
					ok=False
		if ok:		
			for person in isUnaffected:
				if people[person]=='homoAlt':
					ok=False
		if ok:
			inList.append(codename)
		return ok,ok,inList
	def testDominant(people,isParent,isAffected,isUnaffected,isMother,inList,codename):
		"""
		Rules:
		affecteds are not homozygous reference
		unaffecteds are homozygous reference
		>=1 parent is het
		"""
		ok=True
		hetCount=0
		for person in isParent:
			if people[person]=='het':
				hetCount+=1
		if hetCount==0:
			ok=False
		
		if ok:
			for person in isAffected:
				if people[person]=='homoRef':
					ok=False
		if ok:
			for person in isUnaffected:
				if people[person]!='homoRef':
					ok=False
		if ok:
			
			inList.append(codename)
		return ok,ok,inList
	def testDenovo(people,isParent,isAffected,isUnaffected,isMother,inList,codename):
		"""
		Rules:
		Affecteds are hets
		Unaffecteds are homo ref
		Parents are homo ref
		"""
		ok=True
		for person in isAffected:
			if people[person]=='homoRef':
				ok=False
		for person in isUnaffected:
			if people[person]!='homoRef':
				ok=False
		for person in isParent:
			if people[person]!='homoRef':
				ok=False
		if ok:
			
			inList.append(codename)
		return ok,ok,inList
	def testxlinked(people,isParent,isAffected,isUnaffected,isMother,inList,codename):
		"""
		Rules:
		mother is het
		affecteds are homozygous alternate
		"""
		ok=True
		for person in isMother:
			if people[person] != 'het':
				ok=False
		if ok:
			for person in isAffected:
				if people[person] != 'homoAlt':
					ok=False
		
		if ok:
			inList.append(codename)
		return ok,ok,inList
	def testCompHets(variantDict,isParent):
		
		compHets=dict()
		for gene in variantDict.keys():
			if len(variantDict[gene])>1: #Check if there are at least 2 hets in affecteds (this dict includes only variants where all affecteds are hets)
				ok=True
				foundParents=[]
				for variant in variantDict[gene]:
					codename=variant[1]
					people=variant[0]
					for person in isParent: #Check that no parent is homoAlt
						if people[person]=='homoAlt':
							ok=False
						if people[person]=='het':
							foundParents.append(person)
				
				#Check that no parent contains ALL of the variants
				for parent in isParent:
					count=foundParents.count(parent)
					if count==len(variantDict[gene]):
						ok=False
				if ok:
					compHets[gene]=variantDict[gene]
		return compHets
						
	isParent=[] #Individs that are parents of an affected individual
	isAffected=[] 
	isUnaffected=[] 
	isMother=[]
	for line in open(pedFile):
		if len(line)>3 and line[0] != '#':
			line=line.strip('\n').split('\t')
			individ=line[1]
			if line[5]=='1':
				isUnaffected.append(individ)
			
			if line[5]=='2':
				isAffected.append(individ)
				if line[2] not in isParent:
					isParent.append(line[2])
				if line[3] not in isParent:
					isParent.append(line[3])
					isMother.append(line[3])
	
	#Get individ columns
	colIndivid=dict()
	
	for line in open(vcfFile):
		if line[:2]=='#C':
			line=line.strip('\n').split('\t')
			cPos=9
			for column in line[9:]:
				colIndivid[cPos]=column
				cPos+=1

			break
	
	
	#Test each variant
	recessiveVariants=[]
	dominantVariants=[]
	xlinkedVariants=[]
	denovoVariants=[]
	
	variantsInGene=mdict()
	
	variantDict=dict()
	
	for line in open(vcfFile):
		if line[0]!='#':
			
			people=dict()
			tooFewReads=False
			line=line.strip('\n').split('\t')
			try:
				
				readDepth=int(line[7].split('DP=')[1].split(';')[0])
				
			except IndexError: readDepth=0

			
			cPos=9
			for column in line[9:]:
				column=column.split(':')
				
				
				dp=int(column[2])
				if dp<readDepthCutoff:
					tooFewReads=True
					
				genotype=column[0]
			
				if genotype=='1/1':
					genotype='homoAlt'
				elif genotype=='0/1':
					genotype='het'
				elif genotype=='0/0':
					genotype='homoRef'
				else:
					tooFewReads=True
				if genotype in ['homoAlt','het','homoRef']:
					ind=colIndivid[cPos]
					people[ind]=genotype
						
				
			
				cPos+=1	
			
			codename=line[0] + '.'+	line[1]
			
			#Get family descption for output to database
			familyDescription=''
			for person in people.keys():
				familyDescription = familyDescription+ person + ':' + people[person] + ' '
			
			variantDict[codename]=familyDescription
			if not tooFewReads:			
				variantDetails=line[7]
				
				gene=variantDetails.split('EFF=')[1].split('|')[5]
				if len(gene)>0:
					for variantType in importantEffects:
						if variantDetails.find(variantType)>-1:
							ok=True
							for person in isAffected:
								if people[person]!='het': #To be considered for compound het, must be het in all Affecteds.
									ok=False
							if ok:	
								variantsInGene[gene]=(people,codename)
				
				if line[0] != 'X':
					isRecessive,done,recessiveVariants=testRecessive(people,isParent,isAffected,isUnaffected,isMother,recessiveVariants,codename)
					
					if not done:
						isDominant,done,dominantVariants=testDominant(people,isParent,isAffected,isUnaffected,isMother,dominantVariants,codename)
					if not done:
						isDenovo,done,denovoVariants=testDenovo(people,isParent,isAffected,isUnaffected,isMother,denovoVariants,codename)
				if line[0]=='X':
					isxlinked,done,xlinkedVariants=testxlinked(people,isParent,isAffected,isUnaffected,isMother,xlinkedVariants,codename)

	compHets=testCompHets(variantsInGene,isParent)
	
	return recessiveVariants,dominantVariants,xlinkedVariants,denovoVariants,compHets,variantDict
while True:
	
	for browseFolder in browseFolders:
		completed=getCompletedRuns()
	
		folders=os.listdir(browseFolder)
		
		for folder in folders:
			if folder not in completed:
				filesToDelete=[]
				if os.path.isdir(browseFolder + folder):
					
					family=folder
					
					dataFolder=browseFolder + folder #This is where data and ped files are stored
					folder = 'data/' + folder #This is where working files are generated and stored
					if not os.path.isdir(folder):
						os.mkdir(folder)
						
						
					#Scan through all files, make sure not still copying. If still copying, leave this family for now
					for i in ['0','1']:
						vars()['files' + i]=dict()
						for file in os.listdir(dataFolder + '/'):
							vars()['files' + i][file]=os.path.getsize(dataFolder + '/' + file)
						time.sleep(2)
					
					ok=True
					for file in files1.keys():
						try:
							if files1[file] != files0[file]:
								ok=False
								writeToLog(logFile,'Waiting for ' + family + ' files to finish copying')
						except KeyError: 
							ok=False
							writeToLog(logFile,'Waiting for ' + family + ' files to finish copying')
					
					if ok:
						#print family
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
									#Check if sorted. If not, sort.
									samtoolsCheckCommand='samtools view -H ' + dataFolder + '/' + file + ' > tmp/samt.txt'
									os.system(lsamtoolsCheckCommand)
									for line in open('tmp/samt.txt'):
										if line.strip('\n').split(':')[-1]=='coordinate':
											bamFiles = bamFiles + dataFolder + '/' + file
										else:
											samtoolsSortCommand='samtools sort ' + dataFolder + '/' + file + ' tmp/' + file'
											writeToLog(logFile,samtoolsSortCommand)
											os.system(samtoolsSortCommand)
											filesToDelete=append('tmp/' + file)
											bamFiles = bamFiles + 'tmp/' + file
										break
									
									numBamFiles+=1
						
							if len(bamFiles)==0:
								#figure out what mapping parameters Baylor uses. Copy those, make BAM from FASTQ
								writeToLog(logFile,dataFolder + ' - No bam files found')
								ok=False
							if len(bamFiles)>0:					
								#The BAM files we currently get from Baylor are already realigned over INDELS
								# (see https://www.broadinstitute.org/gatk/guide/tooldocs/org_broadinstitute_gatk_tools_walkers_indels_IndelRealigner.php, 
								#  https://www.broadinstitute.org/gatk/guide/tooldocs/org_broadinstitute_gatk_tools_walkers_indels_RealignerTargetCreator.php)
								#When setting up to use with FASTQ files, add use of these tools 
								
								
								
								
								#Generate VCF file
								gatkCommand=java7Location + ' -jar ~/gatk/gatk-protected/dist/GenomeAnalysisTK.jar -T UnifiedGenotyper'
								bamFilesList=bamFiles.split(' ')
								for bamFile in bamFilesList:
									gatkCommand=gatkCommand + ' -I ' + bamFile
								gatkCommand = gatkCommand + ' -R ' + genomeLocation
								gatkCommand = gatkCommand + ' -nct 3 -o data/' + family + '/' +  family + '.vcf --output_mode EMIT_VARIANTS_ONLY'
								writeToLog(logFile,gatkCommand)
								os.system(gatkCommand)
						if ok:	
							#Get PED file
							pedLocation,ok=getPedFile(dataFolder,folder,family,logFile,numBamFiles)
						
							
						
						if ok:
							checkPedFile(pedLocation,'data/' +family + '/' + family + '.vcf') #Check if individs in vcf == PED. If not, try to rewrite PED based on VCF individs.

							
							if not skipEarly:
								#zlessCommand= 'zless ' + folder  + '/' +  family  + '.vcf | sed s/ID=AD,Number=./ID=AD,Number=R/  | vt decompose -s - | vt normalize -r ' + genomeLocation + ' - | java -Xmx4G -jar snpEff.jar GRCh37.75 -formatEff -classic | bgzip -c > data/' + family + '/' +  family +  '.vcf.gz'
								zlessCommand= 'zless ' + folder  + '/' +  family  + '.vcf | sed s/ID=AD,Number=./ID=AD,Number=R/ | java -Xmx4G -jar snpEff.jar GRCh37.75 -formatEff -classic | bgzip -c > data/' + family + '/' +  family +  '.vcf.gz'
								writeToLog(logFile,zlessCommand)
								
								os.system(zlessCommand)
								
								os.system('cp snpEff_summary.html ' + folder  + '/')
								writeToLog(logFile,'snpEff_summary.html copied to ' + folder)
								
								tabixCommand='tabix -p vcf ' + folder  +  '/' +  family  + '.vcf.gz'
								writeToLog(logFile,tabixCommand)
								os.system(tabixCommand)
							#Extract annotated VCF file
							gunzipCommand='gunzip -f -k ' + folder  +  '/' +  family  + '.vcf.gz'
							writeToLog(logFile,gunzipCommand)
							os.system(gunzipCommand)
							#Get variants that segregate in each inheritence mode. 
							recessiveVariants,dominantVariants,xVariants,denovoVariants,compHets,variantDict=selectVariants(pedLocation,'data/' + family + '/' +  family + '.vcf')
							writeToLog(logFile,'Identified ' + str(len(dominantVariants)) + ' dominant variants, ' + str(len(recessiveVariants)) + ' recessive variants, ' + str(len(xVariants)) + ' X-linked variants, ' + str(len(denovoVariants)) + ' de novo variants, and ' + str(len(compHets.keys())) + ' compound heterozygous variants.')
							#Get variant codes for variants that are part of compound heterozygotes
							refCodesToUse=dict()
							for gene in compHets:
								for i in compHets[gene]:
									refCodesToUse[i[1]] = gene
								
							skipEarly=False
							if os.path.isfile('db/' +  family  + '.db'): #If vcf file is already generated, use that. If you don't want to use the old file, delete it.
								skipEarly=True
								writeToLog(logFile,'Using previous db file for ' + family)
							
							if not skipEarly:
								#geminiLoadCommand='gemini load --cores 2 -v ' + folder  + '/' +  family  + '.vcf.gz -t snpEff -p ' + pedLocation + ' db/' + family  + '.db'
	
								writeToLog(logFile,geminiLoadCommand)
								os.system(geminiLoadCommand + ' > tempOut.txt')
								#for line in open('tempOut.txt'):
								#	writeToLog(logFile,line.strip('\n'))
								if not os.path.isfile('db/'+ family  + '.db'):
									ok=False
									writeToLog(logFile,family + ' Gemini load failed - check family file')
							#Filter variants
							if ok:
								#If no cutoffs.xlsx, add default
								if not os.path.isfile(dataFolder + '/cutoffs.xlsx'):
									copyfile('database/cutoffs.xlsx', 'data/' + family + '/cutoffs.xlsx')
					
								
								
								#output all annotated variants and add to universal database
	
								writeToLog(logFile,family +' variants outputting to tmp/variants.txt')
								os.system('gemini query -q \"select * from variants\" --header db/' + family + '.db > tmp/variants.txt')
								
								
								#Start unfiltered variant file and print header
								write=open('data/' + family + '/variantsUnfiltered.txt','w')
								write.writelines('Inheritence\tFamily members\tGene\t')
								for line in open('tmp/variants.txt'):
									write.writelines(line)
									break
								pos=0
								con = lite.connect('db/all.db')
								writeToLog(logFile,family +' variants being added to all.db database')
								
								compHetsToWrite=mdict()
								
								cur = con.cursor()  
								foundCodes=[]
								for line in open('tmp/variants.txt'):
									if pos==0:
										head=line.strip('\n').split('\t')
										headText='INSERT INTO variants (family_id'
			
										for h in head:
											headText=headText + ',' + h
										headText=headText + ',family_segregation) VALUES ( '
		
									else:
										values=line.strip('\n').split('\t')
										refCode=values[0].strip('chr') + '.' + str(int(values[1])+1) 
										if refCode in refCodesToUse.keys():
											gene=refCodesToUse[refCode]
											compHetsToWrite[gene]='compHet\t' + variantDict[refCode] + '\t' + gene + '\t' + line
											foundCodes.append(refCode)
										command=headText + '\'' + family + '\''
										for v in values:
											command = command + ',\'' + v.replace('\'','') + '\''
										try:
											command=command + ',\'' + variantDict[refCode] + '\');'
											
											cur.execute(command)
										except KeyError: pass
										#Make variant code (chr.spot+1.ref.alt)
										
										for segregationMode in ('recessive','dominant','x','denovo'):
											varList=vars()[segregationMode + 'Variants']
											if refCode in varList: #Check if this variant is in my lists of co-segregating variants
												write.writelines(segregationMode + '\t' + variantDict[refCode] + '\t' + values[57] + '\t' + line)
												break
										
										
									pos=1
								
								
								con.commit()	
								con.close()
								
								
								
								write.close()
								writeToLog(logFile,family +' database addition completed')
								
								filterCommand='python filterVariants.py ' + family + ' ' + 'data/' + family + '/variantsUnfiltered.txt ' + 'data/' + family + '/' +'filtered_' + family + 'Variants.tsv ' + 'data/' + family + '/cutoffs.xlsx'
								os.system(filterCommand)
								writeToLog(logFile,filterCommand)
								with open('data/' + family + '/' +'filtered_' + family + 'Variants.tsv', 'r') as content_file:
									content = content_file.read()
								write=open('data/' + family + '/' +'filtered_' + family + 'Variants.tsv','w')
								#write log info here
								versionHeader=getVersionInfo()
								write.writelines(versionHeader)
								write.writelines(content)
								for gene in compHetsToWrite.keys():
									for variant in compHetsToWrite[gene]:
										write.writelines(variant)
											
								
								#os.remove('tmp/variants.txt')
							
							if ok:
								completed=getCompletedRuns()
								completed.append(family)
								writeCompleted = open('completedRuns.txt','w')		
								for fam in completed:
									writeCompleted.writelines('\n' + fam)
								writeCompleted.close()
								#print family  +' completed'
								writeToLog(logFile,family  + ' completed')
				for file in filesToDelete:
					os.remove(file)
							
	time.sleep(120)

