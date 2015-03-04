import getopt
import os
import subprocess
import sys


def create_makefile():
	#  make file
	makefile = """
PROGRAM = ${binary}

SMMDIR=/home/jcai/Documents/smm/stack_manager/lib

INCLUDEDIRS=-I$(SMMDIR)
INCLUDE=-include stack_manager.h
LIBDIRS=
LIBS = -lm

OBJECTS = stack_manager.bc ${objectsUnfold}
CC=clang
CFLAGS = $(INCLUDEDIRS) $(INCLUDE) -O0
LDFLAGS = $(LIBDIRS) $(LIBS) -static -Wl,-T,spm.ld

all: $(PROGRAM)

$(PROGRAM): $(OBJECTS)
	llvm-link -o $@.bc $(OBJECTS)
	$(CC) -o $@ $@.bc $(LDFLAGS)
	llvm-dis < $@.bc > $@.ll
	llc -march=cpp $@.ll -o $@_ll.cpp
	objdump -d $@ > $@.dis
	opt -load /home/jcai/Applications/llvm/build/Debug+Asserts/lib/LLVMSmmStack.so -smm-stack < $@.bc > $@_opt.bc
	$(CC) $@_opt.bc -o $@_opt $(LDFLAGS) 
	llvm-dis < $@_opt.bc > $@_opt.ll
	objdump -d $@_opt > $@_opt.dis

stack_manager.bc:$(SMMDIR)/stack_manager.c
	$(CC) -emit-llvm -c $(CFLAGS) $< -o $@

%.bc: %${sourceFileExtension}
	$(CC) -emit-llvm -c $(CFLAGS) $< -o $@

clean:
	-rm -rf  $(PROGRAM) $(PROGRAM)_opt *s. *.o *.bc *.ll *_ll.cpp *.dis *.txt m5out	
    """

	# Create the linker script for SPM setup
	if (not os.path.isfile("spm.ld")): 
		with open('spm.ld', 'w') as outFile:
			inFile = subprocess.Popen("ld --verbose", stdout=subprocess.PIPE, shell=True).communicate()[0].split("\n")
			i = 0
			while i <  range(len(inFile)):
		    		line = inFile[i]
    				while (line.find("==================================================") == -1):
					i = i+1
					line = inFile[i]
				i = i + 1
    				line = inFile[i]
				while (line.find("==================================================") == -1):
    					outFile.write(line + "\n")
					if line.find("executable_start") != -1:
					  	outFile.write("  _spm_begin = .;\n  . = . + 0x100000;\n  _spm_end = .;\n")
					i = i+1
					line = inFile[i]
				break;

	# Create the makefile using the created linker script
	if (not os.path.isfile("Makefile")): 
		cwd = os.getcwd()
		files = os.listdir(cwd)
		objects = []
		sourceFileExtension = ""
		for i in range(len(files)):
			(file, extension) = os.path.splitext(files[i])
			if(extension == ".c" or extension == ".cpp" or extension == ".cc"):
				objects.append(file)
				if sourceFileExtension == "":
					sourceFileExtension = extension
		objects = list(set(objects))
		objectsUnfold = ""
	   	for i in range(len(objects)):
			objectsUnfold = objectsUnfold + " " + objects[i] + ".bc"
		# Use the name of current folder as the name of generated binary file
		binary = os.path.basename(cwd)
		with open('Makefile', 'w') as f:
			makefile = makefile.replace("${objectsUnfold}", objectsUnfold)
			makefile = makefile.replace("${binary}", binary)
			makefile = makefile.replace("${sourceFileExtension}", sourceFileExtension)
			f.write(makefile)


def create_runme(arguments="", output=""):
	binary = os.path.basename(os.getcwd())
	# Create a runme script
	if (not os.path.isfile("rumme.sh")):
		with open("runme.sh", "w") as f:
			text = "#!/bin/sh\nSIMDIR=$HOME/Applications/smm_gem5\n$SIMDIR/build/X86/gem5.debug $SIMDIR/configs/example/se.py --cpu-type=atomic -c " + binary
			if (arguments != ""):
				text = text + " -o \"" + arguments + "\""
			if (output != ""):
				text = text + " --output=\"" + output + "\""
			f.write(text + "\n")


# Get options
if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "-h", ["help", "make", "args=", "output=", "run", "clean"]) 
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)
	arguments = ""
	output = ""
	needToCreateRunme = 0
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print 'smm --make --run --clean'
			sys.exit()
		elif opt in ("--make"):
			create_makefile()
		elif opt in ("--args"):
			arguments = arg
		elif opt in ("--output"):
			output = arg
		elif opt in ("--run"):
			needToCreateRunme = 1
		elif opt in ("--clean"):
			if (os.path.isfile("spm.ld")):
    				subprocess.Popen("rm spm.ld", stdout=subprocess.PIPE, shell=True)
			if (os.path.isfile("Makefile")):
    				subprocess.Popen("rm Makefile", stdout=subprocess.PIPE, shell=True)
			if (os.path.isfile("runme.sh")):
    				subprocess.Popen("rm runme.sh", stdout=subprocess.PIPE, shell=True)
		else:
			assert False, "unhandled option"
		if needToCreateRunme:
			create_runme(arguments, output)
