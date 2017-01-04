'''
Templates to write classes with methods in ActionScript
'''

CLASST = '''
package
{{
	public class {classname} {extends}
	{{
		{methodbodies}
	}}
}}
'''

FUNCTIONT = '''
{override} public function {name}():String{{
    var k: String = '{classname}' + '{s2}';
    return k;
}}
'''

LOOPVART = 'var i:int = 0;'

VART = '''
var _{classname}:{classname} = new {classname};
'''

CALLT = '''
for (i = 0; i < {limit}; i++)
{{
    _{classname}.{method}();
}}
'''

CALL_BOILERPLATE_PRE = '''
package
{

	public class SubjectWrapper implements ISubjectWrapper
	{

		public function SubjectWrapper()
		{
		}

		public function subject():Boolean
		{


'''
CALL_BOILERPLATE_POST = '''
			return true;
		}
	}
}
'''
