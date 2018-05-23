from flask import Flask, request, redirect, flash, jsonify
import werkzeug

from reader.app import get_flashed_messages_by_prefix, APIThing, APIError


app = Flask(
    __name__,
    template_folder='reader/templates',
    static_folder='reader/static',
)
app.secret_key = 'secret'
app.template_global()(get_flashed_messages_by_prefix)


@app.route('/')
def root():
    return app.jinja_env.from_string("""

{% import "macros.html" as macros %}

<!doctype html>

<meta name="viewport" content="width=device-width" />
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='controls.js') }}"></script>


<script>

window.onload = function () {

    register_all({{ url_for('form') | tojson | safe }});

};

</script>


<form action="{{ url_for('form') }}" method="post">
<ul class="controls">

{% call macros.simple_button('simple', 'simple') %}
    document.querySelector('#out').innerHTML = JSON.stringify(data);
{% endcall %}
{% call macros.confirm_button('confirm', 'confirm', 'confirm') %}
    document.querySelector('#out').innerHTML = JSON.stringify(data);
{% endcall %}
{% call macros.text_input_button('text', 'text', 'text', 'text') %}
    document.querySelector('#out').innerHTML = JSON.stringify(data);
{% endcall %}

{% call macros.simple_button('simple', 'simple2', leave_disabled=true) %}
    document.querySelector('#out').innerHTML = "v2: " + JSON.stringify(data);
{% endcall %}
{% call macros.confirm_button('confirm', 'confirm2', 'confirm2', leave_disabled=true) %}
    document.querySelector('#out').innerHTML = "v2: " + JSON.stringify(data);
{% endcall %}
{% call macros.text_input_button('text', 'text2', 'text', 'text', leave_disabled=true) %}
    document.querySelector('#out').innerHTML = "v2: " + JSON.stringify(data);
{% endcall %}

{% for message in get_flashed_messages_by_prefix(
    'simple',
    'confirm',
    'text',
) %}
<li class="error">{{ message }}
{% endfor %}

</ul>

<input type="hidden" name="next" value='{{ url_for('root', from='next') }}'>
<input type="hidden" name="next-simple" value='{{ url_for('root', from_action='next-simple') }}'>
<input type="hidden" name="next-confirm" value='{{ url_for('root', from_action='next-confirm') }}'>
<input type="hidden" name="next-text" value='{{ url_for('root', from_action='next-text') }}'>

</form>


{% for message in get_flashed_messages_by_prefix('message') %}
<pre>{{ message }}</pre>
{% endfor %}

<pre id='out'></pre>


""").render()





form = APIThing(app, '/form', 'form')

@form
def simple(data):
    return 'simple'

@form(really=True)
def confirm(data):
    return 'confirm'

@form
def text(data):
    text = data['text']
    if text.startswith('err'):
        raise APIError(text, 'category')
    return 'text: %s' % text


