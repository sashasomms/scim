# Hunter Abraham
# June 2020
# Convert Acqknowledge DINs (event markers) to txt
# OUTPUT: Tab-separated file with the following columns:
# NID (index) | Time (in seconds) | Name (Event that occured, e.g. CalibrationStart, BlockStart, 100msTrialStart, 200msTrialStart)

# Sasha note May 2022: Task code does not seem to have sent the correct signal to Biopac for the block start.


def find_all_files(directory, list_of_files):
	pattern = "n[0-9]{4}\.acq$"
	for root, dirs, files in os.walk(directory):
		if "old" in root:
			continue
		for name in files:
			if ((re.search(pattern, name) is not None)):
				if root.endswith("/"):
					list_of_files.append(str(root) + str(name))
				else:
					list_of_files.append(str(root) + "/" + str(name))
		for direct in dirs:
			find_all_files(direct, list_of_files)
	return list_of_files

t_0 = time.time()
parent_dir = "../../raw-data/interoception/psychophys/" 
list_of_paths = []

list_of_paths = find_all_files(parent_dir, list_of_paths)
print("[INFO] Paths captured: ")
for path in list_of_paths:
	print("       " + path)

out_parent_dir = "../../processed-data/interoception/psychophys/"
out_parent_dir_restore = out_parent_dir
for path in list_of_paths:
	out_parent_dir = out_parent_dir_restore	
	print("[INFO] Processing file: {}".format(path))
	out_parent_dir += path.split("/")[len(path.split("/")) - 2] + "/raw_converted_to_txt/"	
	print(out_parent_dir)
	if not os.path.exists(os.path.dirname(out_parent_dir)):
		try:
			os.makedirs(os.path.dirname(out_parent_dir))
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	
	out_parent_dir += "{}_interoception000{}_markers.txt".format(path.split("/")[len(path.split("/")) - 2], path[len(path) - 5])
	print("[INFO] File outputting to: {}".format(out_parent_dir))
	# Process data
	data = bioread.read_file(path)
	f_index = 0
	channel_mapping = {9:0, 10:100, 11:200, 12:300, 13:400, 14:500}
	not_used_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16]
	# Used channels: {9, 10, 11, 12, 13, 14}
	f_out = open(out_parent_dir, "w+")
	f_out.write("nid\ttime_seconds\tevent_type\n")
	for i, chan in enumerate(data.channels):
		if i in not_used_channels:
			continue
		print("[INFO] Processing channel {}".format(i))
		# Here we have one channel
		is_on = 0
		prev = 0
		# Iterate through channel values
		for j, reading in enumerate(chan.data):
			# Check to see if it went to '1'
			prev = is_on
			is_on = reading
		
			if is_on != prev:
				# write to file
				if is_on == 5:
					f_out.write("{}\t{}\t{}msTrialStart\n".format(f_index, chan.time_index[j], channel_mapping[i]))
				elif is_on == 0:
					f_out.write("{}\t{}\t{}msTrialEnd\n".format(f_index, chan.time_index[j], channel_mapping[i]))		
	
	f_out.close()