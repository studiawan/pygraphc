from operator import itemgetter
import subprocess

# initialization
replaced = {'[': '\[', ']': '\]', '/': '\/', '$': '\$', '"': '\"', '*': '\*'}
clusters = {}
cluster_index = 0
properties = {}
properties['log_path'] = '/home/hudan/Git/labeled-authlog/dataset/Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all/messages'

# get outlier line numbers as a independent cluster
outlier_file = 'messages.logcluster_outlier.txt'
with open(outlier_file, 'r') as f:
	outliers = f.readlines()

outliers_member = []
for outlier in outliers:
	for k, v in replaced.iteritems():
		outlier = outlier.replace(k, v)
	
	cat = subprocess.Popen(('cat', properties['log_path']), stdout=subprocess.PIPE)
	grep = subprocess.Popen(('grep', '-xn', outlier), stdin=cat.stdout, stdout=subprocess.PIPE)
	with open('/tmp/line_number.txt', 'w') as fi:
		cut = subprocess.Popen(('cut', '-f1', '-d:'), stdin=grep.stdout, stdout=fi)		
	cat.wait()
	grep.wait()
	cut.wait()
	
	with open('/tmp/line_number.txt', 'r') as fi:
		member_line = fi.readline()			
	outliers_member.append(member_line.rstrip())

# get line number id for outlier clusters
clusters[cluster_index] = [int(x) - 1 for x in outliers_member]
cluster_index += 1

# get abstraction per line and cluster member
with open('messages.logcluster_output.txt', 'r') as f:
	lines = f.readlines()

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
abstractions = []
for line in lines:
	if line.startswith('Support:'):
		total_member = int(line.split(': ')[1])
		line_splits.insert(0, total_member)						
		line_splits.insert(0, len(line_splits) - 1)		
		abstractions.append(line_splits)
		
	else:
		line = line.strip()
		line_splits = line.split('|')
		if line_splits:
			for line_split in line_splits:
				for month in months:
					# check day with single digit					
					if line_split.startswith(month):
						extract_day = line_split.split()						
						day = extract_day[1]						
						if int(day) < 10:							
							day = ' ' + day							
							extract_day.remove(extract_day[1])
							extract_day.insert(1, day)							
							new_line_split = ' '.join(extract_day)
							
							index = line_splits.index(line_split)
							line_splits.remove(line_split)
							line_splits.insert(index, new_line_split)
				# if empty
				if line_split == '':
					line_splits.remove(line_split)
							
# build big cluster
big_clusters = {}
for a in abstractions:
	if a[2] not in big_clusters.keys():
		big_clusters[a[2]] = []
		big_clusters[a[2]].append(a)
	else:
		big_clusters[a[2]].append(a)

# sort based on frequency
for key, value in big_clusters.iteritems():
	sorted_value = sorted(value, key=itemgetter(0), reverse=True)
	big_clusters[key] = sorted_value
	
# get member per cluster
for key, values in big_clusters.iteritems():		
	for value in values:				
		commands = []
		commands.append(['cat', properties['log_path']])
		for index, abstraction_split in enumerate(value[2:]):				
			for k, v in replaced.iteritems():
				abstraction_split = abstraction_split.replace(k, v)			
			if index == 0:
				commands.append(['grep', '-n', abstraction_split])			
			else:
				commands.append(['grep', abstraction_split])
		commands.append(['cut', '-f1', '-d:'])				
		
		# run commands 
		total_command = len(commands)
		popen_list = []
		for index, command in enumerate(commands):
			if index == 0:
				popen_list.append(subprocess.Popen(command, stdout=subprocess.PIPE)) 
			elif index == total_command - 1:
				with open('/tmp/line_number.txt', 'w') as fi:
					popen_list.append(subprocess.Popen(command, stdin=popen_list[index - 1].stdout, stdout=fi)) 
			else:
				popen_list.append(subprocess.Popen(command, stdin=popen_list[index - 1].stdout, stdout=subprocess.PIPE)) 
			
			if index > 0:
				popen_list[index - 1].stdout.close()	
		
		# wait for all subprocess end
		for p in popen_list:
			p.wait()
		
		# match total cluster member
		with open('/tmp/line_number.txt', 'r') as fi:
			member_lines = fi.readlines()

		# check for members in other clusters		
		member_lines = [int(x) - 1 for x in member_lines]
		total_member = len(member_lines)				
		if value[1] != total_member:									
			for index, cluster in clusters.iteritems():			
				member_lines = list(set(member_lines) - set(cluster))
			total_member = len(member_lines)
			if value[1] != total_member:
				print 'After evaluation', value[1], total_member, commands			

		# save clusters
		clusters[cluster_index] = member_lines
		cluster_index += 1
		
		print total_member, value
