
package
{
	
	public class SubjectWrapper implements ISubjectWrapper
	{
		
		public function SubjectWrapper()
		{
		}
		
		public function subject():Boolean
		{
			var i:int = 0;
			var _C1:C1 = new C1;
			
			var _C11:C11 = new C11;
			
			for (i = 0; i < 2; i++)
			{
				_C1.work1();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C1.work2();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C1.work3();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C1.work4();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C11.work1();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C11.work2();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C11.work3();
			}
			
			for (i = 0; i < 2; i++)
			{
				_C11.work4();
			}
			return true;
		}
	}
}
