#!/usr/bin/env python3
"""
Datawrapper Chart Skill — main orchestrator.
Creates, configures, publishes, and exports Datawrapper charts via API.
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.datawrapper.de/v3"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB Datawrapper limit
API_TIMEOUT = 30
EXPORT_RETRY_DELAY = 2
EXPORT_MAX_RETRIES = 3
PUBLISH_SETTLE_DELAY = 1


class ApiError(Exception):
    """Custom exception for API errors with retryability info."""
    def __init__(self, error_type, message, status_code=None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.retryable = status_code in (429, 502, 503, 504)


def get_api_key():
    key = os.environ.get("DATAWRAPPER_API_KEY", "")
    if not key:
        fail("auth_error", "DATAWRAPPER_API_KEY not set. Get one at https://app.datawrapper.de/account/api-tokens")
    return key


def fail(error_type, message):
    print(json.dumps({"ok": False, "error": {"type": error_type, "message": message}}, ensure_ascii=False))
    sys.exit(1)


def api_request(method, path, api_key, data=None, content_type="application/json", accept="application/json"):
    url = f"{API_BASE}{path}" if path.startswith("/") else path
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": accept,
    }

    body = None
    if data is not None:
        if content_type == "application/json":
            body = json.dumps(data).encode("utf-8")
        elif content_type == "text/csv":
            body = data.encode("utf-8") if isinstance(data, str) else data
        headers["Content-Type"] = content_type

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            ct = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in ct:
                return json.loads(raw)
            elif "image/" in ct:
                return raw  # binary PNG
            else:
                return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")[:300]
        if e.code == 401:
            raise ApiError("auth_error", f"401 Unauthorized. Check API key and scopes. {body_text}", 401)
        elif e.code == 403:
            raise ApiError("auth_error", f"403 Forbidden. Token may lack required scopes. {body_text}", 403)
        elif e.code == 429:
            raise ApiError("rate_limit", f"429 Rate limited. Try again later. {body_text}", 429)
        else:
            raise ApiError("api_error", f"HTTP {e.code}: {body_text}", e.code)
    except urllib.error.URLError as e:
        raise ApiError("network_error", f"Network error: {e.reason}")
    except Exception as e:
        raise ApiError("network_error", str(e))


def load_data(args):
    """Load and normalize input data to CSV string."""
    raw = None
    input_format = args.input_format or "auto"

    if args.data_file:
        if not os.path.exists(args.data_file):
            fail("input_error", f"File not found: {args.data_file}")
        file_size = os.path.getsize(args.data_file)
        if file_size > MAX_FILE_SIZE:
            fail("input_error", f"File too large: {file_size / 1024 / 1024:.1f}MB (max 10MB)")
        with open(args.data_file, "r", encoding="utf-8") as f:
            raw = f.read()
        if input_format == "auto":
            if args.data_file.endswith(".json"):
                input_format = "json"
            else:
                input_format = "csv"
    elif args.data_inline:
        raw = args.data_inline
    else:
        fail("input_error", "Provide --data-file or --data-inline")

    if input_format == "auto":
        raw_stripped = raw.strip()
        if raw_stripped.startswith("[") or raw_stripped.startswith("{"):
            input_format = "json"
        elif "|" in raw_stripped.split("\n")[0] and "," not in raw_stripped.split("\n")[0]:
            input_format = "table"
        else:
            input_format = "csv"

    if input_format == "csv":
        result = raw
    elif input_format == "json":
        result = json_to_csv(raw)
    elif input_format == "table":
        result = pipe_table_to_csv(raw)
    else:
        result = raw

    # Validate non-empty
    if not result or not result.strip():
        fail("input_error", "Data is empty after processing")

    return result


def json_to_csv(raw):
    """Convert JSON array of objects to CSV."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        fail("input_error", f"Invalid JSON: {e}")

    if isinstance(data, dict):
        if "columns" in data and "rows" in data:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(data["columns"])
            for row in data["rows"]:
                writer.writerow(row)
            return output.getvalue()
        else:
            fail("input_error", "JSON object must have 'columns' and 'rows' keys")

    if not isinstance(data, list) or len(data) == 0:
        fail("input_error", "JSON must be a non-empty array of objects")

    keys = list(data[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=keys)
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    return output.getvalue()


def pipe_table_to_csv(raw):
    """Convert pipe-delimited table to CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or set(line.replace("|", "").replace("-", "").strip()) == set():
            continue  # skip separator lines
        cells = [c.strip() for c in line.split("|") if c.strip()]
        writer.writerow(cells)
    return output.getvalue()


def create_chart(api_key, chart_type, title=None, theme=None, folder_id=None):
    """Step 1: Create chart."""
    payload = {"type": chart_type}
    if title:
        payload["title"] = title
    if theme:
        payload["theme"] = theme
    if folder_id:
        payload["folderId"] = folder_id
    return api_request("POST", "/charts", api_key, data=payload)


def upload_data(api_key, chart_id, csv_data):
    """Step 2: Upload CSV data."""
    return api_request("PUT", f"/charts/{chart_id}/data", api_key,
                       data=csv_data, content_type="text/csv")


def patch_chart(api_key, chart_id, patch_data):
    """Step 3: Apply metadata/customization."""
    return api_request("PATCH", f"/charts/{chart_id}", api_key, data=patch_data)


def publish_chart(api_key, chart_id):
    """Step 4: Publish."""
    return api_request("POST", f"/charts/{chart_id}/publish", api_key)


def export_png(api_key, chart_id, output_dir, zoom=2, width=None, height=None,
               plain=False, transparent=False, border_width=20):
    """Step 5: Export PNG with retry for retryable errors only."""
    params = [
        f"unit=px",
        f"mode=rgb",
        f"plain={'true' if plain else 'false'}",
        f"zoom={zoom}",
        f"borderWidth={border_width}",
    ]
    if transparent:
        params.append("transparent=true")
    if width:
        params.append(f"width={width}")
    if height:
        params.append(f"height={height}")

    query = "&".join(params)

    for attempt in range(EXPORT_MAX_RETRIES):
        try:
            png_data = api_request("GET", f"/charts/{chart_id}/export/png?{query}",
                                   api_key, accept="image/png")
            if isinstance(png_data, bytes) and len(png_data) > 100:
                os.makedirs(output_dir, exist_ok=True)
                png_path = os.path.join(output_dir, f"{chart_id}.png")
                with open(png_path, "wb") as f:
                    f.write(png_data)
                return png_path
            # Small/empty response — chart may not be ready yet
            if attempt < EXPORT_MAX_RETRIES - 1:
                time.sleep(EXPORT_RETRY_DELAY)
                continue
        except ApiError as e:
            if e.retryable and attempt < EXPORT_MAX_RETRIES - 1:
                time.sleep(EXPORT_RETRY_DELAY)
                continue
            fail(e.error_type, e.message)

    return None


def build_metadata(args):
    """Build PATCH payload from args."""
    metadata = {}
    describe = {}
    annotate = {}

    if args.byline:
        describe["byline"] = args.byline
    if args.source_name:
        describe["source-name"] = args.source_name
    if args.source_url:
        describe["source-url"] = args.source_url
    if args.notes:
        annotate["notes"] = args.notes

    if describe:
        metadata["describe"] = describe
    if annotate:
        metadata["annotate"] = annotate

    patch = {}
    if args.title:
        patch["title"] = args.title
    if metadata:
        patch["metadata"] = metadata

    return patch if patch else None


def main():
    parser = argparse.ArgumentParser(description="Datawrapper Chart Creator")
    parser.add_argument("--type", required=True, help="Chart type ID (d3-bars, d3-lines, etc.)")
    parser.add_argument("--data-file", help="Path to CSV or JSON file")
    parser.add_argument("--data-inline", help="Inline CSV/JSON data")
    parser.add_argument("--input-format", choices=["csv", "json", "table", "auto"], default="auto")
    parser.add_argument("--title", help="Chart title")
    parser.add_argument("--publish", action="store_true", help="Publish chart")
    parser.add_argument("--export-png", action="store_true", help="Export PNG after publish")
    parser.add_argument("--output-dir", default="/tmp", help="PNG output directory")
    parser.add_argument("--dark", action="store_true", help="Apply dark theme (uses 'datawrapper-dark' theme ID)")
    parser.add_argument("--theme", help="Datawrapper theme ID (overrides --dark)")
    parser.add_argument("--folder-id", help="Datawrapper folder ID for organization")
    parser.add_argument("--byline", help="Author byline")
    parser.add_argument("--source-name", help="Data source name")
    parser.add_argument("--source-url", help="Data source URL")
    parser.add_argument("--notes", help="Chart notes/annotations")
    parser.add_argument("--width", type=int, help="Export width px")
    parser.add_argument("--height", type=int, help="Export height px")
    parser.add_argument("--png-zoom", type=int, default=2, help="PNG zoom factor")
    parser.add_argument("--png-plain", action="store_true", help="Plain PNG (no header/footer)")
    parser.add_argument("--png-transparent", action="store_true", help="Transparent background")
    parser.add_argument("--png-border-width", type=int, default=20, help="PNG border width")

    args = parser.parse_args()

    api_key = get_api_key()

    # 1. Load and validate data
    csv_data = load_data(args)

    # 2. Create chart
    # Note: 'datawrapper-dark' may not exist on all accounts.
    # Use --theme with your custom theme ID if dark mode fails.
    theme = args.theme or ("datawrapper-dark" if args.dark else None)
    try:
        chart_resp = create_chart(api_key, args.type, title=args.title, theme=theme, folder_id=args.folder_id)
    except ApiError as e:
        fail(e.error_type, e.message)

    chart_id = chart_resp.get("id")
    if not chart_id:
        fail("api_error", f"No chart ID in response: {chart_resp}")

    # 3. Upload data
    try:
        upload_data(api_key, chart_id, csv_data)
    except ApiError as e:
        fail(e.error_type, e.message)

    # 4. Patch metadata
    patch_data = build_metadata(args)
    if patch_data:
        try:
            patch_chart(api_key, chart_id, patch_data)
        except ApiError as e:
            fail(e.error_type, e.message)

    # 5. Publish
    public_url = None
    embed_url = None
    if args.publish:
        try:
            pub_resp = publish_chart(api_key, chart_id)
        except ApiError as e:
            fail(e.error_type, e.message)
        pub_data = pub_resp if isinstance(pub_resp, dict) else {}
        public_url = pub_data.get("data", {}).get("publicUrl", "")
        if public_url and public_url.startswith("//"):
            public_url = f"https:{public_url}"
        embed_url = public_url

    # 6. Export PNG
    png_path = None
    if args.export_png:
        if not args.publish:
            fail("input_error", "Must --publish before --export-png")
        time.sleep(PUBLISH_SETTLE_DELAY)  # let publish propagate
        png_path = export_png(
            api_key, chart_id, args.output_dir,
            zoom=args.png_zoom, width=args.width, height=args.height,
            plain=args.png_plain, transparent=args.png_transparent,
            border_width=args.png_border_width
        )

    # Result
    result = {
        "ok": True,
        "chart_id": chart_id,
        "chart_type": args.type,
        "edit_url": f"https://app.datawrapper.de/chart/{chart_id}/visualize",
        "public_url": public_url,
        "embed_url": embed_url,
        "png_path": png_path,
        "warnings": [],
        "applied_config": {
            "theme": theme,
            "dark": args.dark,
            "publish": args.publish,
            "export_png": args.export_png,
        }
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
