"""
Constants for the experiment concerning reordering method calls
"""
DEBUG = False

PROJECTS_PATH = 'D:\\Studie\\Master\\ExperimentationProject\\SourceProjects'
ORIGIN_PROJECT = 'NameResolution'
SA_PLAYERS = [
    'flashplayer9r280_win_sa.exe',
    'flashplayer_23_sa.exe',
]
FF_PATH = 'C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe'
HTML_WRAP_TEMPLATE = """
<html><head></head><body>
<script>
function send_marker(finishing){{
    document.title = (finishing ? 'Finished' : 'Aborting') + ', sending mark'
    var xhr = new XMLHttpRequest();
    var attempts = 0;
    var id = setInterval(function(){{
        xhr.open('GET', "http://{host}:5000/mark", false);
        xhr.setRequestHeader('Access-Control-Allow-Headers', '*');
        xhr.setRequestHeader('Access-Control-Allow-Origin', '*');
        xhr.send();
        if (++attempts === 10){{
            window.clearInterval(id);
            console.log('Stopped trying sending finished-mark');
        }}
        console.log(xhr.response, xhr.status);
        if(xhr.response == '1' && xhr.status == 200){{
            document.title = (finishing ? 'Done' : 'Aborted') + ' - Close me';
            window.clearInterval(id);
            if(finishing){{
                var element = document.getElementById("abort-btn");
                element.parentNode.removeChild(element);
            }}
        }}
    }}, 750)
}}
function window_close(){{
    send_marker(true)
}}
function abort(){{
    send_marker(false)
}}</script>
<object width="640" height="480" data="{swf_file}"></object>
<button type="button" onclick="this.style.visibility='hidden'; abort()" id="abort-btn">Abort</button>
</body></html>
"""
FLASH_PROFILE_ITERATIONS = 20
FLASH_SECS_FOR_RUN = 5
TEST_TARGETS = range(1, 50 + 1)

if not DEBUG:
    NUM_BASE_CLASSES = 8
    NUM_SUB_CLASSES = NUM_BASE_CLASSES
    NUM_METHODS = 50
    TOTAL_CALLS = 400 * 1000
    NUM_BLOCKS = 4
else:
    NUM_BASE_CLASSES = 1
    NUM_SUB_CLASSES = NUM_BASE_CLASSES
    NUM_METHODS = 10
    TOTAL_CALLS = 10 * 1000
    NUM_BLOCKS = 2
