import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from jinja2 import Environment
from ansible.plugins.filter.core import FilterModule as CoreFilters
from ansible.plugins.filter.mathstuff import FilterModule as MathFilters
from ansible.plugins.filter.urls import FilterModule as UrlFilters

import os
import time
import threading
import signal

HOST = 'localhost'
PORT = 8000

env = Environment(
  trim_blocks=True,
  lstrip_blocks=True
)
env.filters.update(CoreFilters().filters())
env.filters.update(MathFilters().filters())
env.filters.update(UrlFilters().filters())

class JinjaHandler(BaseHTTPRequestHandler):
  data_store = {}

  def _send_headers(self, status=200, content_type='text/html', extra_headers=None):
    self.send_response(status)
    self.send_header('Content-type', content_type)
    self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
    self.send_header('Pragma', 'no-cache')
    self.send_header('Expires', '0')
    if extra_headers:
      for key, value in extra_headers.items():
        self.send_header(key, value)
    self.end_headers()

  def do_GET(self):
    self._send_headers()
    self.wfile.write("""
    <html>
    <head>
      <title>Jinja2 Web Evaluator</title>
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.css">
      <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/codemirror.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/jinja2/jinja2.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/javascript/javascript.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/xml/xml.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.13/mode/yaml/yaml.min.js"></script>
      <style>
        .CodeMirror {
          border: 1px solid #ccc;
          height: auto;
          min-height: 150px;
          resize: both;
          overflow: auto;
          font-family: monospace;
          font-size: 14px;
        }
        #jsoninput, #jinjaexpr {
          width: 90%;
          height: 150px;
          resize: both;
        }
        .note {
          font-style: italic;
          font-size: 14px;
          color: #555;
          margin-bottom: 10px;
        }
        #history-list {
          margin-top: 10px;
        }
        #history-list button {
          margin: 0 5px 5px 0;
        }
      </style>
    </head>
    <body>
      <h2>JSON Data (Ansible output)</h2>
      <form id="upload-form" enctype="multipart/form-data">
        <input type="file" id="jsonfile" name="jsonfile">
        <button type="submit">Load JSON</button>
      </form>
      <textarea id="jsoninput"></textarea>

      <div id="history-list"></div>

      <h2>Jinja Expression</h2>
      <div class="note">The variable <code>data</code> contains the full JSON input.</div>
      <textarea id="jinjaexpr"></textarea>

      <h2>Result <small id="result-type"></small></h2>
      <select id="result-mode">
        <option value="application/json">JSON</option>
        <option value="text/plain">Plain text</option>
        <option value="text/x-yaml">YAML</option>
        <option value="application/xml">XML</option>
      </select>
      <textarea id="resultview" readonly></textarea>

      <script>
      let jinjaEditor, resultEditor;

      function updateHistory(fileName, content) {
        let history = JSON.parse(localStorage.getItem('jsonHistory') || '[]');
        history.unshift({name: fileName, content: content});
        history = history.slice(0, 3);
        localStorage.setItem('jsonHistory', JSON.stringify(history));
        renderHistory();
      }

      function renderHistory() {
        let history = JSON.parse(localStorage.getItem('jsonHistory') || '[]');
        const container = $('#history-list');
        container.html('<strong>Recent Files:</strong><br>');
        history.forEach((item, index) => {
          container.append(`<button data-index="${index}">${item.name}</button>`);
        });
      }

      $(document).ready(function() {
        jinjaEditor = CodeMirror.fromTextArea(document.getElementById("jinjaexpr"), {
          mode: "jinja2",
          lineNumbers: true,
          lineWrapping: true,
          indentWithTabs: false,
          tabSize: 2
        });
        jinjaEditor.setSize("90%", '100px');

        const storedExpr = localStorage.getItem('lastExpr');
        jinjaEditor.setValue(storedExpr || '{{ data }}');

        $('#upload-form').on('submit', function(e) {
          e.preventDefault();
          var file = $('#jsonfile')[0].files[0];
          var reader = new FileReader();
          reader.onload = function(e) {
            const content = e.target.result;
            $('#jsoninput').val(content);
            jinjaEditor.setValue(jinjaEditor.getValue());
            updateHistory(file.name, content);
          }
          if (file) reader.readAsText(file);
        });

        $('#history-list').on('click', 'button', function() {
          const index = $(this).data('index');
          const history = JSON.parse(localStorage.getItem('jsonHistory') || '[]');
          const item = history[index];
          if (item) {
            $('#jsoninput').val(item.content);
            jinjaEditor.setValue(jinjaEditor.getValue());
          }
        });

        jinjaEditor.on('change', function() {
          sendRender();
        });

        $('#jsoninput').on('input', function() {
          sendRender();
        });

        $('#result-mode').on('change', function() {
          const mode = $(this).val();
          resultEditor.setOption('mode', mode);
        });

        resultEditor = CodeMirror.fromTextArea(document.getElementById("resultview"), {
          mode: "application/json",
          lineNumbers: true,
          readOnly: true,
          lineWrapping: true,
          indentWithTabs: false,
          tabSize: 2
        });
        resultEditor.setSize("90 %", 1000);

        function sendRender() {
          $.post('/render', {
            json: $('#jsoninput').val(),
            expr: jinjaEditor.getValue()
          }, function(data, status, xhr) {
            const resultType = xhr.getResponseHeader('X-Result-Type') || 'string';
            $('#result-type').text(`(${resultType})`);
            try {
              const parsed = JSON.parse(data);
              const pretty = JSON.stringify(parsed, null, 2);
              resultEditor.setValue(pretty);
              localStorage.setItem('lastExpr', jinjaEditor.getValue());
            } catch (e) {
              resultEditor.setValue(data);
            }
          }).fail(function(xhr) {
            resultEditor.setValue('Error: ' + xhr.responseText);
            $('#result-type').text('(error)');
          });
        }

        renderHistory();
        sendRender();
      });
      </script>
      <br/><br/><br/><br/><br/><br/><br/><br/><br/>
    </body>
    </html>
    """.encode())

  def do_POST(self):
    if self.path != '/render':
      self._send_headers(404)
      self.wfile.write(b"Not found")
      return

    content_length = int(self.headers['Content-Length'])
    post_data = self.rfile.read(content_length)
    params = parse_qs(post_data.decode())
    json_text = params.get('json', [''])[0]
    expr = params.get('expr', [''])[0]

    try:
      data = json.loads(json_text)
    except Exception as e:
      self._send_headers(400, 'text/plain')
      self.wfile.write(f"JSON parsing error: {e}".encode())
      return

    try:
      template = env.from_string(expr)
      output = template.render(data=data)
      try:
        parsed = json.loads(output)
        output = json.dumps(parsed, indent=2)
        self._send_headers(200, 'text/plain', {'X-Result-Type': 'json'})
      except:
        self._send_headers(200, 'text/plain', {'X-Result-Type': 'string'})
      self.wfile.write(output.encode())
    except Exception as e:
      self._send_headers(400, 'text/plain')
      self.wfile.write(f"Jinja expression error: {e}".encode())

if __name__ == '__main__':
  import subprocess
  import threading
  import time
  import os

  def watch_file(path):
    last_mtime = os.path.getmtime(path)
    while True:
      time.sleep(1)
      try:
        mtime = os.path.getmtime(path)
        if mtime != last_mtime:
          print("Reloading server due to file change...")
          os.execv(sys.executable, [sys.executable] + sys.argv)
      except Exception:
        continue

  threading.Thread(target=watch_file, args=(__file__,), daemon=True).start()

  print(f"Server started at http://{HOST}:{PORT}")
  server = HTTPServer((HOST, PORT), JinjaHandler)
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    print("\nShutting down server.")
    server.server_close()
