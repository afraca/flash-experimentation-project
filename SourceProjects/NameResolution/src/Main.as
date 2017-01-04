package
{
	import flash.display.Sprite;
	import flash.events.Event;
	import flash.utils.getTimer;
	import flash.text.TextField;
	import flash.text.TextFieldAutoSize;
	import flash.text.TextFormat;
	import flash.system.Capabilities;
	import flash.system.System;
	import flash.external.ExternalInterface;
	import flash.system.Security;
	import flash.events.HTTPStatusEvent;
	
	public class Main extends Sprite
	{
		private var label:TextField;
		
		public function Main()
		{
			configureLabel();
			this.label.text = 'Starting profiling';
			// In closures we cannot access this, so use reference
			var rLabel:TextField = this.label;
			var postAssertion:Function = function(success:Boolean, errorEvent:Event = null):void
			{
				var onSuccess:Function = function():void
				{
					var iterations:int = 20;
					var wrapper:SubjectWrapper = new SubjectWrapper();
					profile(wrapper.subject, 0, iterations);
				}
				
				if (success)
				{
					onSuccess()
				}
				else
				{
					if (Capabilities.version.indexOf('MAC') == 0)
					{
						// Force through on Mac...
						onSuccess()
					}
					else
					{
						var msg:String = 'Logger not running on http://' + ProfileResult.loggerHost + ':5000';
						trace(msg);
						rLabel.text = msg;
					}
				}
				return;
			}
			// Possible format {name}_{compId}_{optimized} with optionally 'wrap-' in front for html
			var filename:String;
			var urlArray:Array
			
			if (Capabilities.playerType == 'StandAlone')
			{
				urlArray = this.loaderInfo.url.split('/');
				filename = urlArray[urlArray.length - 1].split('.swf')[0];
			}
			else if (Capabilities.playerType == 'PlugIn')
			{
				urlArray = ExternalInterface.call("window.location.href.toString").split('/');
				filename = urlArray[urlArray.length - 1].split('.html')[0];
				// Drop the 'wrap-'
				filename = filename.slice(5);
			}
			else
			{
				throw new Error('Invalid playerType: ' + Capabilities.playerType);
			}
			// By default it gets url encoded
			filename = unescape(filename)
			var extra:Array = filename.split('_');
			if (extra.length > 1)
			{
				ProfileResult.project = extra[0];
				ProfileResult.optimized = extra[2];
				ProfileResult.config = extra[3];
			}
			else
			{
				// Not part of our pipeline
				ProfileResult.project = filename;
			}
			
			ProfileResult.setCompiler(NAMES::compiler);
			ProfileResult.setLoggerHost(NAMES::loggerHost);
			Security.allowDomain('*');
			//Security.loadPolicyFile('http' + ProfileResult.loggerHost + ':5000/crossdomain.xml');
			ProfileResult.assertLoggerRunning(postAssertion);
		}
		
		private function configureLabel():void
		{
			label = new TextField();
			label.autoSize = TextFieldAutoSize.LEFT;
			label.background = true;
			label.border = true;
			
			var format:TextFormat = new TextFormat();
			format.font = "Verdana";
			format.color = 0xFF0000;
			format.size = 14;
			format.underline = true;
			
			label.defaultTextFormat = format;
			addChild(label);
		}
		
		protected function profile(toProfile:Function, currentIteration:int, maxIterations:int):void
		{
			var benchOk:Boolean = false;
			var start:int = getTimer();
			// The ACTUAL execution
			benchOk = toProfile();
			var end:int = getTimer();
			var msg:String;
			
			if (benchOk)
			{
				var result:ProfileResult = new ProfileResult(end - start);
				msg = 'Making request to log execution time of ' + result.elapsed + 'ms for subject';
				// In closures we cannot access this, so use reference
				var rLabel:TextField = this.label;
				rLabel.text = msg;
				trace(msg);
				
				// Because we only register this function as callback once in ProfileResult, pass iteration through there
				var logDone:Function = function(success:Boolean, currentIteration:int = -1, error:String = null):void
				{
					var msg:String;
					if (!success)
					{
						msg = 'Logging failed: ' + error;
						rLabel.text = msg;
						trace(msg);
					}
					else
					{
						if (currentIteration == maxIterations - 1)
						{
							msg = maxIterations + ' iterations have been completed';
							rLabel.text = msg;
							trace(msg);
							close();
						}
						else
						{
							profile(toProfile, currentIteration + 1, maxIterations);
						}
					}
				}
				result.writeOut(logDone, currentIteration);
			}
			else
			{
				msg = 'Profiling subject returned error code';
				trace(msg);
				this.label.text = msg;
			}
		}
		
		protected function close():void
		{
			if (Capabilities.playerType == 'StandAlone')
			{
				System.exit(0);
			}
			else if (Capabilities.playerType == 'PlugIn')
			{
				ExternalInterface.call('window_close');
			}
			else
			{
				throw new Error('Runtime not supported for experiment');
			}
		}
	
	}

}