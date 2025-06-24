import requests
import subprocess
import shutil
import json
import os
import sys
import socket
import threading
import webbrowser
from urllib.parse import urlparse
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn, TextColumn

console = Console()

def premium_banner():
    console.print(Panel.fit(
        "[bold magenta]Auto Video Link Converter[/bold magenta]",
        subtitle="by zerosocialcode",
        style="bold green"
    ), justify="center")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

def find_free_port(start=8000, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found.")

def write_html_file(links, title, filename="video_links.html"):
    # Group links by title for batch mode
    from collections import defaultdict
    sections = defaultdict(list)
    for link in links:
        section_title = link.get("title") or title or link.get("source") or "Direct Download Links"
        sections[section_title].append(link)

    html = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Video Links</title>',
        '''<style>
            body { font-family: system-ui, sans-serif; margin: 1.2em; background: #f6f8fa;}
            h2 { font-size: 1.15em; margin-top: 1.4em; }
            .table-wrap { overflow-x: auto; }
            table { border-collapse: collapse; width: 100%; min-width: 350px; background: #fff;}
            th, td { padding: 0.7em 0.4em; text-align: left; font-size: 1em;}
            th { background: #222a3f; color: #fff;}
            tr:nth-child(even) { background: #f3f5f7; }
            a { color: #2196F3; word-break: break-all; font-weight: 500; }
            @media (hover: hover) and (pointer: fine) {
                a:hover { text-decoration: underline; }
            }
            @media (max-width: 600px) {
                body { font-size: 1em; margin: 0.5em; }
                h2 { font-size: 1em;}
                table, th, td { font-size: 0.98em; }
                th, td { padding: 0.5em 0.18em; }
            }
            @media (max-width: 400px) {
                table, th, td { font-size: 0.92em; }
                th, td { padding: 0.3em 0.05em; }
            }
        </style>''',
        '</head>',
        '<body>'
    ]

    for section_title, links_in_section in sections.items():
        html.append(f'<h2>Direct Download Links for: {section_title}</h2>')
        html.append('<div class="table-wrap"><table>')
        html.append('<tr><th>#</th><th>Resolution</th><th>Size</th><th>File</th></tr>')
        for link in links_in_section:
            # Generate a nice file name for the anchor text
            safe_title = section_title.replace('/', '_').replace('\\', '_').replace(' ', '_')
            res = str(link.get("resolution") or "")
            ext = ".mp4" if ".mp4" in link["url"] else ""
            # Try to extract file name from URL if possible, else generate one
            from urllib.parse import unquote
            import re
            url_filename = unquote(link["url"].split('/')[-1].split('?')[0])
            if url_filename and (url_filename.endswith(".mp4") or url_filename.endswith(".webm")) and len(url_filename) < 80:
                file_name = url_filename
            else:
                file_name = f"{safe_title}-{res}{ext}"
            html.append(
                f'<tr>'
                f'<td>{link["number"]}</td>'
                f'<td>{res}</td>'
                f'<td>{link["size"]}</td>'
                f'<td><a href="{link["url"]}" target="_blank">{file_name}</a></td>'
                f'</tr>'
            )
        html.append('</table></div>')
    html.append('</body></html>')
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return filename

def serve_forever(directory, filename, port):
    import http.server
    import socketserver
    os.chdir(directory)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        sys.stdout = open(os.devnull, 'w')  # Silence server output
        try:
            console.print(f"[green]Server running! Press [bold]Ctrl+C[/bold] to stop.[/green]")
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[cyan]Server stopped. Bye![/cyan]")

def launch_server(directory, filename, port):
    url = f"http://localhost:{port}/{filename}"
    t = threading.Thread(target=serve_forever, args=(directory, filename, port), daemon=False)
    t.start()
    return url

def format_filesize(filesize):
    try:
        if not filesize:
            return ""
        mb = int(filesize) / (1024 * 1024)
        return f"{mb:.1f} MB"
    except Exception:
        return ""

def present_formats_plain(formats, title, source=None, base_idx=1):
    links = []
    if title:
        console.print(f"\n[bold]Direct Download Links for: {title}[/bold]\n")
    else:
        console.print(f"\n[bold]Direct Download Links[/bold]\n")
    console.print(f"{'No.':<4}{'Res/Note':<14}{'Size':<10}URL")
    console.print("-" * 80)
    shown = 0
    for i, f in enumerate(formats, base_idx):
        if f.get('vcodec') == 'none':
            continue
        url = f.get('url')
        if url and ('.m3u8' in url or '.mpd' in url or 'manifest' in url):
            continue
        resolution = f.get("format_note", "") or f.get("height", "")
        if isinstance(resolution, int):
            resolution = f"{resolution}p"
        filesize = format_filesize(f.get("filesize") or f.get("filesize_approx"))
        if url:
            console.print(f"{i:<4}{str(resolution):<14}{filesize:<10}[blue]{url}[/blue]")
            links.append({
                'number': i,
                'title': title,
                'resolution': resolution,
                'size': filesize,
                'url': url
            })
            shown += 1
    if shown == 0:
        console.print("[yellow]No downloadable video formats found (only streams). Use yt-dlp to download streams.[/yellow]")
    return links

def universal_fallback(url, title=None, base_idx=1):
    links = []
    try:
        resp = requests.get(url, allow_redirects=True, timeout=15)
        content_type = resp.headers.get("content-type", "")
        if "html" in content_type:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            sources = []
            for tag in soup.find_all(["video", "source"]):
                src = tag.get("src")
                if src:
                    try:
                        head = requests.head(src, allow_redirects=True, timeout=10)
                        size = format_filesize(head.headers.get("content-length"))
                    except Exception:
                        size = ""
                    sources.append((src, size))
            if sources:
                console.print("\n[bold]Direct Download Links[/bold]\n")
                console.print(f"{'No.':<4}{'Size':<10}URL")
                console.print("-" * 80)
                for i, (src, size) in enumerate(sources, base_idx):
                    console.print(f"{i:<4}{size:<10}[blue]{src}[/blue]")
                    links.append({
                        'number': i,
                        'title': title,
                        'resolution': '',
                        'size': size,
                        'url': src
                    })
                return links
    except Exception as e:
        console.print(f"[red]Fallback extraction error: {e}[/red]")
    console.print("[yellow]No downloadable video formats found.[/yellow]")
    return links

def run_yt_dlp_with_progress(url, cmd):
    json_output = ""
    error_lines = []
    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("[yellow]Processing video link...", total=None)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        for line in proc.stdout:
            json_output += line
            if '[download]' in line and '%' in line:
                try:
                    percent_str = line.split('%')[0].split()[-1]
                    percent = float(percent_str)
                    if progress.tasks[task].total is None:
                        progress.update(task, total=100)
                    progress.update(task, completed=percent)
                    progress.update(task, description="[green]Extracting formats...")
                except Exception:
                    pass
            if line.strip().startswith("ERROR:") or line.strip().startswith("Error:"):
                error_lines.append(line)
        proc.wait()
        progress.update(task, completed=100)
        progress.update(task, description="[cyan]Done!")
    return json_output, error_lines

def get_yt_dlp_formats_with_progress(url, cookies=None, username=None, password=None):
    if not shutil.which("yt-dlp"):
        return None, "yt-dlp is not installed"
    cmd = ["yt-dlp", "-J", "--no-warnings", "--newline", url]
    if cookies:
        cmd += ["--cookies", cookies]
    if username:
        cmd += ["-u", username]
    if password:
        cmd += ["-p", password]
    output, error_lines = run_yt_dlp_with_progress(url, cmd)
    if error_lines:
        return None, "\n".join(error_lines)
    try:
        info = json.loads(output)
        return info, None
    except Exception as e:
        try:
            json_part = output[output.rfind('{'):]
            info = json.loads(json_part)
            return info, None
        except Exception:
            return None, f"Failed to parse yt-dlp output: {e}"

def process_single_link(url, cookies=None, username=None, password=None, base_idx=1):
    links = []
    title = url
    while True:
        info = None
        yt_dlp_error = None
        try:
            info, yt_dlp_error = get_yt_dlp_formats_with_progress(
                url, cookies=cookies, username=username, password=password
            )
        except Exception as e:
            yt_dlp_error = str(e)

        if yt_dlp_error:
            err = yt_dlp_error.lower()
            if "cookies" in err or "cookie" in err:
                cookies = Prompt.ask("[bold red]This video requires authentication cookies. Enter path to your cookies.txt[/bold red]").strip()
                continue
            elif "login" in err or "username" in err or "password" in err:
                username = Prompt.ask("[bold red]This video requires login. Enter your username/email[/bold red]").strip()
                password = Prompt.ask("[bold red]Enter your password[/bold red]", password=True).strip()
                continue
            elif "unsupported url" in err or "no extractor" in err:
                console.print("[yellow]yt-dlp could not handle this link. Trying fallback method...[/yellow]")
                links = universal_fallback(url, title=title, base_idx=base_idx)
                break
            elif "yt-dlp is not installed" in err:
                console.print("[red]yt-dlp is not installed. Please install yt-dlp and try again.[/red]")
                return [], url
            else:
                console.print(f"[red]yt-dlp error: {yt_dlp_error}[/red]")
                break

        if info:
            formats = info.get("formats", [])
            title = info.get("title", "") or url
            links = present_formats_plain(formats, title, source=url, base_idx=base_idx)
            # Patch: Also set 'title' attr in each link for grouping in HTML
            for l in links:
                l['title'] = title
            if not links:
                links = universal_fallback(url, title=title, base_idx=base_idx)
            break
    return links, title

def main():
    premium_banner()
    mode = Prompt.ask(
        "[bold green]Choose mode[/bold green] ([b]1[/b]=Single link, [b]2[/b]=Batch from urls.txt)",
        choices=["1", "2"], default="1"
    )

    all_links = []
    all_titles = []

    if mode == "1":
        url = Prompt.ask("[bold yellow]Paste your video link[/bold yellow]").strip()
        if not is_valid_url(url):
            console.print("[red]Invalid URL. Please enter a valid video link (starting with http or https).[/red]")
            return
        links, title = process_single_link(url)
        all_links.extend(links)
        all_titles.append(title)
    else:
        inputfile = Prompt.ask("[bold yellow]Enter path to batch URL file[/bold yellow]", default="urls.txt")
        if not os.path.exists(inputfile):
            console.print(f"[red]File not found: {inputfile}[/red]")
            return
        with open(inputfile, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        if not urls:
            console.print(f"[red]No URLs found in {inputfile}[/red]")
            return
        idx = 1
        for url in urls:
            if not is_valid_url(url):
                console.print(f"[yellow]Invalid URL skipped: {url}[/yellow]")
                continue
            console.print(f"\n[cyan]Processing: {url}[/cyan]")
            links, title = process_single_link(url, base_idx=idx)
            all_links.extend(links)
            all_titles.append(title)
            idx += len(links)
        if not all_links:
            console.print("[red]No downloadable video links found in batch.[/red]")
            return

    htmlfile = "video_links.html"
    try:
        write_html_file(all_links, "Batch Conversion Results" if len(all_titles) > 1 else all_titles[0], htmlfile)
        console.print(f"\n[green]Links saved to [bold]{htmlfile}[/bold] in this directory.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save HTML file: {e}[/red]")
        return

    answer = Prompt.ask("[cyan]Do you want to host this file to localhost for clickable links? (y/n)[/cyan]", choices=["y", "n"], default="n")
    if answer.lower() == "y":
        try:
            port = find_free_port()
            url_localhost = f"http://localhost:{port}/{htmlfile}"
            console.print(f"\n[green]Hosted! Visit:[/green] [bold blue]{url_localhost}[/bold blue]\n")
            try:
                webbrowser.open_new_tab(url_localhost)
            except Exception:
                pass
            serve_forever(os.getcwd(), htmlfile, port)
        except Exception as e:
            console.print(f"[red]Failed to start server: {e}[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[cyan]Bye![/cyan]")
