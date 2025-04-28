
from fc_exceptions import *;

def test_console():
	py_out("this is std.out");
	py_err("this is std.err");
	
def test_pure_data():
	PD['ERROR']("hello","world");
	PD['WARNING']("hello","world");
	PD['NOTICE']("hello","world");
	PD['MESSAGE']("hello","world");
	PD['LOG']("hello","world");

def test_free_cad():
	FC['ERROR']("hello","world");
	FC['WARNING']("hello","world");
	FC['NOTICE']("hello","world");
	FC['MESSAGE']("hello","world");
	FC['LOG']("hello","world");	

def test_wb():
	Workbench['ERROR']("hello","world");
	Workbench['WARNING']("hello","world");
	Workbench['NOTICE']("hello","world");
	Workbench['MESSAGE']("hello","world");
	Workbench['LOG']("hello","world");

def test_raise_exception( some_exception,level,message):
	try:
		raise some_exception(level,message);
	except Exception as e:
		print(type(e).__name__, e.args);



if __name__ == '__main__':
	
	test_console();
	print();
	
	test_pure_data();
	print();
	
	test_free_cad();
	print();
	
	test_wb();
	print();
	
	test_raise_exception(PureDataException,0,"Hello World");
	print();
	
	test_raise_exception(FreeCADException,0,"Hello World");
	print();
	
	test_raise_exception(WorkBenchException,0,"Hello World");
	print();
	
	class CustomException(PureDataException):
		
		def __init__(self,*args):
			PureDataException.__init__(self,'WARNING',*args);
	
	
	test_raise_exception(CustomException,"Hello","World");
	print();
	
