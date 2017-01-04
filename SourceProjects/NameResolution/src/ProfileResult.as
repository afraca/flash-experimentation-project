package
{
	import flash.display.Loader;
	import flash.events.IOErrorEvent;
	import flash.events.TimerEvent;
	import flash.net.URLLoader;
	import flash.events.HTTPStatusEvent;
	import flash.net.URLRequest;
	import flash.net.URLVariables;
	import flash.system.Capabilities;
	import flash.utils.Timer;
	import flash.display.Stage;
	;
	
	public class ProfileResult
	{
		public var elapsed:int;
		protected var version:String;
		protected var standalone:int;
		
		protected static var loader:URLLoader;
		public static var loggerHost:String;
		public static var writeOutIteration:int;
		public static var project:String;
		public static var compiler:String;
		public static var optimized:int;
		public static var config:String
		
		public function ProfileResult(elapsed:int)
		{
			this.elapsed = elapsed;
			this.version = Capabilities.version;
			this.standalone = Capabilities.playerType == 'StandAlone' ? 1 : 0;
		}
		
		public function writeOut(callback:Function, writeOutIteration:int):void
		{
			// So we can slightly tweak the callback, even though it's only set once
			ProfileResult.writeOutIteration = writeOutIteration;
			if (!ProfileResult.loader.hasEventListener(IOErrorEvent.IO_ERROR))
			{
				ProfileResult.loader.addEventListener(IOErrorEvent.IO_ERROR, function(event:IOErrorEvent):void
				{
					callback(false, -1, event);
				});
				var onSuccess:Function = function(event:HTTPStatusEvent):void
				{
					if (event.status != 200)
					{
						callback(false, -1, event);
					}
					else
					{
						// Flash will mess up when requests are too quick after eachother (?!)
						var timer:Timer = new Timer(250);
						timer.addEventListener(TimerEvent.TIMER, function():void
						{
							timer.stop();
							callback(true, ProfileResult.writeOutIteration);
						});
						timer.start();
					}
				
				}
				ProfileResult.loader.addEventListener(HTTPStatusEvent.HTTP_STATUS, onSuccess);
			}
			
			var url:String = 'http://' + ProfileResult.loggerHost + ':5000';
			var variables:URLVariables = new URLVariables();
			variables.elapsed = this.elapsed;
			variables.version = this.version;
			variables.standalone = this.standalone;
			variables.optimized = ProfileResult.optimized || 0;
			variables.compiler = ProfileResult.compiler;
			variables.project = ProfileResult.project;
			variables.config = ProfileResult.config;
			var request:URLRequest = new URLRequest(url);
			request.data = variables;
			
			ProfileResult.loader.load(request);
		}
		
		public static function assertLoggerRunning(callback:Function):void
		{
			ProfileResult.loader = new URLLoader();
			// For errors don't bother un-registering
			var requestWentBad:Function = function(event:IOErrorEvent):void
			{
				callback(false, event);
			};
			var checkLogPingResult:Function = function(event:HTTPStatusEvent):void
			{
				if (event.status != 200)
				{
					callback(false, event);
				}
				else
				{
					ProfileResult.loader.removeEventListener(HTTPStatusEvent.HTTP_STATUS, checkLogPingResult);
					ProfileResult.loader.removeEventListener(IOErrorEvent.IO_ERROR, requestWentBad);
					callback(true);
				}
			}
			ProfileResult.loader.addEventListener(IOErrorEvent.IO_ERROR, requestWentBad);
			ProfileResult.loader.addEventListener(HTTPStatusEvent.HTTP_STATUS, checkLogPingResult);
			ProfileResult.loader.load(new URLRequest('http://' + ProfileResult.loggerHost + ':5000/ping'));
		}
		
		public static function setCompiler(input:String = '?'):void
		{
			ProfileResult.compiler = input;
		}
		
		public static function setLoggerHost(input:String = 'localhost'):void
		{
			// Compiler option messes up string somehow...
			var pattern:RegExp = /\'/g
			ProfileResult.loggerHost = input.replace(pattern, '');
		}
	}

}