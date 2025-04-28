#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
###################################################################################
#
#  __init__.py
#
#  Copyright 2025 Danilo Mitrovic <danilodanmitrovic+fcpd@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
###################################################################################
__all__ = [];
__version__ = '0.1';
__author__ = "Danillo Mitrovic";
__credits__ = "Florian Foinant-Willig (FCPD),Danilo Mitrovic (fc_exceptions)";

"""
	This python script is intended to bridge error handling from console and FreeCAD in such way that any
	FCPD tooling can be tested/logged independantly of FreeCAD from console in hope to circumvent testing and release of code.
	
	it uses std.out and std.err file streams to they can be easily separated if required.
	
	Informal delimiter is c++ namespace '::' separator so for any csv (comma separated values file, ie excel/libre office) handling
	simply replace any '::' with ';'.
"""

# Handling formatting for console
if "sys" not in globals():
	import sys; # in FreeCAD sys is independantly linked, so no from x import y

py_out = lambda msg: print(msg, file=sys.stdout);
py_err = lambda msg: print(msg, file=sys.stderr);
__all__ += ["py_out","py_err"];


# Handling formatting for FreeCAD
fc_origin	= "FreeCAD";
pd_origin 	= "PureData";
fcpd_origin 	= "FC-PD";

excp_levels = ['ERROR','WARNING','NOTICE','LOG','MESSAGE'];

if 'FreeCAD' not in globals():
	fc_err 		= lambda origin,msg: py_err('::'.join([origin,f"| {excp_levels[0]} |",str(msg)])); 
	fc_wrn 		= lambda origin,msg: py_err('::'.join([origin,f"|{excp_levels[1]}|",str(msg)]));
	fc_inf		= lambda origin,msg: py_out('::'.join([origin,f"| {excp_levels[2]}|",str(msg)]));
	fc_log		= lambda origin,msg: py_out('::'.join([origin,f"|  {excp_levels[3].lower()}  |",str(msg)]));
	fc_msg	 	= lambda origin,msg: py_out('::'.join([origin,f"|{excp_levels[4].lower()}|",str(msg)]));
else:
	def fc_err(origin, message):
		"""
			Free Cad messaging system implemetation for FreeCAD.Console functions.
			Asks for origin (ie <str> of which part of the system is resposnible for message)
			Asks for message (ie <str> of what to display)
			
			Normally format is "origin::| TYPE |::message\n"
			so if any isn't supplied or ('') then:
				 "::| TYPE |::\n"
				 "origin::| TYPE |::\n"
				 "::| TYPE |::message\n"
			
			If FreeCAD isn't loaded, it calls print system cerr or cout depending on a function.
			
			intended use:
				fc_err(fc_origin,message);
			
			can be tested with:
				fc_err('hello','world');
		"""
		packet = '::'.join([str(origin),f"| {excp_levels[0]} |", str(msg),'\n']);
		FreeCAD.Console.PrintError(packet);
		
	def fc_wrn(origin, message):
		"""
			Free Cad messaging system implemetation for FreeCAD.Console functions.
			Asks for origin (ie <str> of which part of the system is resposnible for message)
			Asks for message (ie <str> of what to display)
			
			Normally format is "origin::| TYPE |::message\n"
			so if any isn't supplied or ('') then:
				 "::| TYPE |::\n"
				 "origin::| TYPE |::\n"
				 "::| TYPE |::message\n"
			
			If FreeCAD isn't loaded, it calls print system cerr or cout depending on a function.
			
			intended use:
				fc_wrn(fc_origin,message);
			
			can be tested with:
				fc_wrn('hello','world');
		"""
		packet = '::'.join([str(origin),f"|{excp_levels[1]}|", str(msg),'\n']);
		FreeCAD.Console.PrintWarning(packet);
	
	def fc_inf(origin,message):
		"""
			Free Cad messaging system implemetation for FreeCAD.Console functions.
			Asks for origin (ie <str> of which part of the system is resposnible for message)
			Asks for message (ie <str> of what to display)
			
			Normally format is "origin::| TYPE |::message\n"
			so if any isn't supplied or ('') then:
				 "::| TYPE |::\n"
				 "origin::| TYPE |::\n"
				 "::| TYPE |::message\n"
			
			If FreeCAD isn't loaded, it calls print system cerr or cout depending on a function.
			
			intended use:
				fc_inf(fc_origin,message);
			
			can be tested with:
				fc_inf('hello','world');
		"""
		packet = '::'.join([str(origin),f"| {excp_levels[2]}|", str(msg),'\n']);
		FreeCAD.Console.PrintNotification(packet); # doesn't trigger notice gui.
	
	def fc_log(origin,message):
		"""
			Free Cad messaging system implemetation for FreeCAD.Console functions.
			Asks for origin (ie <str> of which part of the system is resposnible for message)
			Asks for message (ie <str> of what to display)
			
			Normally format is "origin::| TYPE |::message\n"
			so if any isn't supplied or ('') then:
				 "::| TYPE |::\n"
				 "origin::| TYPE |::\n"
				 "::| TYPE |::message\n"
			
			If FreeCAD isn't loaded, it calls print system cerr or cout depending on a function.
			
			intended use:
				fc_log(fc_origin,message);
			
			can be tested with:
				fc_log('hello','world');
		"""
		packet = '::'.join([str(origin),f"|  {excp_levels[3].lower()}  |", str(msg),'\n']);
		FreeCAD.Console.PrintLog(packet);
		
	def fc_msg(origin,message):
		"""
			Free Cad messaging system implemetation for FreeCAD.Console functions.
			Asks for origin (ie <str> of which part of the system is resposnible for message)
			Asks for message (ie <str> of what to display)
			
			Normally format is "origin::| TYPE |::message\n"
			so if any isn't supplied or ('') then:
				 "::| TYPE |::\n"
				 "origin::| TYPE |::\n"
				 "::| TYPE |::message\n"
			
			If FreeCAD isn't loaded, it calls print system cerr or cout depending on a function.
			
			intended use:
				fc_msg(fc_origin,message);
			
			can be tested with:
				fc_msg('hello','world');
		"""
		packet = '::'.join([str(origin),f"|{excp_levels[4].lower()}|", str(msg),'\n']);
		FreeCAD.Console.PrintMessage(packet);

PD = {
	'WARNING'	: lambda *args: fc_wrn(pd_origin,' '.join(map(str,args))),
	'ERROR'		: lambda *args: fc_err(pd_origin,' '.join(map(str,args))),
	'MESSAGE'	: lambda *args: fc_msg(pd_origin,' '.join(map(str,args))),
	'LOG'		: lambda *args: fc_log(pd_origin,' '.join(map(str,args))),
	'NOTICE'	: lambda *args: fc_inf(pd_origin,' '.join(map(str,args))),
};

FC = {
	'WARNING'	: lambda *args: fc_wrn(fc_origin,' '.join(map(str,args))),
	'ERROR'		: lambda *args: fc_err(fc_origin,' '.join(map(str,args))),
	'MESSAGE'	: lambda *args: fc_msg(fc_origin,' '.join(map(str,args))),
	'LOG'		: lambda *args: fc_log(fc_origin,' '.join(map(str,args))),
	'NOTICE'	: lambda *args: fc_inf(fc_origin,' '.join(map(str,args)))
};

Workbench = {
	'WARNING'	: lambda *args: fc_wrn(fcpd_origin,' '.join(map(str,args))),
	'ERROR'		: lambda *args: fc_err(fcpd_origin,' '.join(map(str,args))),
	'MESSAGE'	: lambda *args: fc_msg(fcpd_origin,' '.join(map(str,args))),
	'LOG'		: lambda *args: fc_log(fcpd_origin,' '.join(map(str,args))),
	'NOTICE'	: lambda *args: fc_inf(fcpd_origin,' '.join(map(str,args)))
}

__all__ += ['PD','FC','Workbench'];

if (__debug__ == True): ## for active debugging, activated by default.
	def DEBUG_STATE(state1, state2):
		Workbench['MESSAGE']( f"DEBUGGING : {state1}::{state2}::{state1==state2}" );
	
	def DEBUG_VALUE(value, expected):
		Workbench['LOG']( f"DEBUGGING : {value1}::{value2}" );
	
	def DEBUG_TYPE( obj1, obj2):
		Workbench['NOTICE']( f"DEBUGGING : {type(obj1).__name__}::{type(obj2).__name__}" );

else:
	def DEBUG_STATE(state1, state2):
		pass;
		
	def DEBUG_VALUE(value, expected):
		pass;
	
	def DEBUG_TYPE( obj1, obj2):
		pass;

__all__ += ["DEBUG_STATE","DEBUG_VALUE","DEBUG_TYPE"];

# in console information about exception levels
def print_level_names():
	"""
		There are 5 levels in message handling, and this function prints out all of them with coresponding index.
		So you can refrence by name or by index for any use.
		
		This is used to it can be called from FreeCAD or Python by simply referencing
			fcpd.fc_exceptions.print_level_names 
	"""
	global excp_levels;
	for i,name in enumerate(excp_levels):
		fc_msg(fcpd_origin,f"Level of {i} by name {name}");


# Pure Data Exception with calls to 
class PureDataException (Exception):
	
	"""
		PureDataException is inheriting from WB_BaseException and it handles generating its from by:
			
			__init__(self,level,*args):
				it conjoins with ' ' delimiter all arguments (after converting it to str)
				and then calls respective function to handle the call.
	"""
	
	def __init__(self,level, *args):
		"""
			calls PD[self.level](*args) 
			
				where PD[self.level] cojoins *args into single string (message);
				and self.level is <str> key of internal PD dictionary.
			
			you can see all levels by calling function: 'fc_exceptions.print_level_names'
			
		"""
		if isinstance(level,int):
			level = excp_levels[level % 5];
		if not isinstance(level, str):
			raise TypeError(f"For first argument you can provide either <str> or <int>");
		self.level = level;
		
		PD[self.level](*args);


class FreeCADException (Exception):
	
	"""
		PureDataException is inheriting from WB_BaseException and it handles generating its from by:
			
			__init__(self,level,*args):
				it conjoins with ' ' delimiter all arguments (after converting it to str)
				and then calls respective function to handle the call.
	"""
	
	def __init__(self,level, *args):
		"""
			calls PD[self.level](*args) 
			
				where PD[self.level] cojoins *args into single string (message);
				and self.level is <str> key of internal PD dictionary.
			
			you can see all levels by calling function: 'fc_exceptions.print_level_names'
			
		"""
		if isinstance(level,int):
			level = excp_levels[level % 5];
		if not isinstance(level, str):
			raise TypeError(f"For first argument you can provide either <str> or <int>");
		self.level = level;
		
		FC[self.level](*args);

class WorkBenchException (Exception):
	
	"""
		PureDataException is inheriting from WB_BaseException and it handles generating its from by:
			
			__init__(self,level,*args):
				it conjoins with ' ' delimiter all arguments (after converting it to str)
				and then calls respective function to handle the call.
	"""
	
	def __init__(self,level, *args):
		"""
			calls PD[self.level](*args) 
			
				where PD[self.level] cojoins *args into single string (message);
				and self.level is <str> key of internal PD dictionary.
			
			you can see all levels by calling function: 'fc_exceptions.print_level_names'
			
		"""
		if isinstance(level,int):
			level = excp_levels[level % 5];
		if not isinstance(level, str):
			raise TypeError(f"For first argument you can provide either <str> or <int>");
		self.level = level;
		
		Workbench[self.level](*args);


__all__ += ["print_level_names","PureDataException","FreeCADException","WorkBenchException"];
