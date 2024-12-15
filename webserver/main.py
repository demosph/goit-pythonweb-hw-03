from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader
import urllib.parse
import mimetypes
import pathlib
import json
from datetime import datetime

FILE_PATH = "./storage/data.json"

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        page_url = urllib.parse.urlparse(self.path)
        match page_url.path:
            case "/":
                self.send_html_file("index.html")
            case "/message":
                self.send_html_file("message.html")
            case "/read":
                self.render_template("messages.html", "read.html")
            case _:
                if pathlib.Path(page_url.path[1:]).exists():
                    self.send_static()
                else:
                    self.send_html_file("error.html", 404)

    def do_POST(self):
        try:
            data = self.rfile.read(int(self.headers["Content-Length"]))
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {
                key: value
                for key, value in (el.split("=") for el in data_parse.split("&"))
            }
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            stored_messages = self.read_json(FILE_PATH)
            if not isinstance(stored_messages, dict):
                stored_messages = {}
            stored_messages[time_str] = data_dict

            self.write_json(FILE_PATH, stored_messages)

            self.send_response(302)
            self.send_header("Location", "/read")
            self.end_headers()
        except Exception as e:
            print(f"Error processing POST request: {e}")
            self.send_html_file("error.html", 500)

    def send_html_file(self, filename: str, status: int = 200):
        try:
            self.send_response(status)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(filename, "rb") as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file("error.html", 404)

    def render_template(self, output_file: str, template_file: str):
        try:
            env = Environment(loader=FileSystemLoader("."))
            template = env.get_template(template_file)

            stored_messages = self.read_json(FILE_PATH)
            rendered_content = template.render(messages=stored_messages.values())

            with open(output_file, "w", encoding="utf-8") as fd:
                fd.write(rendered_content)

            self.send_html_file(output_file)
        except Exception as e:
            print(f"Error rendering template: {e}")
            self.send_html_file("error.html", 500)

    def send_static(self):
        try:
            self.send_response(200)
            mt = mimetypes.guess_type(self.path)
            self.send_header(
                "Content-type", mt[0] if mt else "application/octet-stream"
            )
            self.end_headers()
            with open(f".{self.path}", "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_html_file("error.html", 404)

    @staticmethod
    def read_json(filepath: str) -> dict:
        try:
            with open(filepath, "r", encoding="utf-8") as fd:
                return json.load(fd)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def write_json(filepath: str, data: dict):
        try:
            with open(filepath, "w", encoding="utf-8") as fd:
                json.dump(data, fd, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing JSON to {filepath}: {e}")


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        print("Server started at port:", server_address[1])
        print("Press Ctrl+C to stop the server")
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        http.server_close()
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    run()
