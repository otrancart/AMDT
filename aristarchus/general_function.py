import os


def show_available_files(BDIR:str,FOLDER:str):
	""" 
        Get all folders and files in a folder 

        Parameters
        ----------
		BDIR : str
			path to the backup folder
        FOLDER : str
			name of folder to search in

        Returns
        -------
        dictionnary
			key=folder, value=list: filenames(str)
    """
	dir = os.path.join(str(BDIR),str(FOLDER))
	# check if path exists and if FOLDER is a folder
	if (not os.path.exists(dir)) or (not os.path.isdir(dir)):
		return {}

	dirlist = {}
	# for each folder in FOLDER
	for dirname in os.listdir(dir):
		filelist=[]
		d_path = os.path.join(dir, dirname)
		# check if dirname is a folder
		if os.path.isdir(d_path):
			# for each file in folder
			for filename in os.listdir(d_path):
				f = os.path.join(d_path, filename)
				# check filename it is a file
				if os.path.isfile(f) and not (filename.endswith("aux.xml") or filename.endswith(".tfw")):
					# remove extension
					if filename.endswith(".tif"):
						os.rename(f,f.replace(".tif",""))
					filelist.append(filename.replace(".tif",""))
			dirlist[dirname]=filelist
	
	return dirlist



def show_available_files_simple(BDIR:str,FOLDER:str):
	""" 
        Get all files in a folder 

        Parameters
        ----------
		BDIR : str
			path to the backup folder	
    	FOLDER : str
			name of folder to search in

        Returns
        -------
        list(str)
			list of the file names
    """
	dir = os.path.join(str(BDIR),str(FOLDER))
	# check if path exists and if FOLDER is a folder
	if not os.path.exists(dir) or (not os.path.isdir(dir)):
		return []
	
	filelist = []
	# for each file in FOLDER
	for filename in os.listdir(dir):
		f = os.path.join(dir, filename)
		# check if filename is a file
		if os.path.isfile(f) and not (filename.endswith("aux.xml")):
			# remove extension
			if filename.endswith(".tif"):
				os.rename(f,f.replace(".tif",""))
			filelist.append(filename.replace(".tif",""))
	
	return filelist
