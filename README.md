# Log Analyzer

**Simple GUI tool to analyze API failure logs** - Select a connector, pick a log file, get a report.

## Why I Built This

I work at **Keepit** analyzing lots of API logs every day. Manually searching through thousands of lines for failures was killing me.

So I took the **initiative** and built this small Python tool. Now I can:

1. Select a **Connector** (e.g. Jira)
2. Click **Browse** → pick a log file
3. Click **GENERATE REPORT** → done!
4. Click **Open Report Folder** to jump straight to the output

## Quick Start

```
git clone https://github.com/VasilisKokotakis/Log-Analyzer.git
cd Log-Analyzer
python3 main.py
```

## Requirements
- Python 3.8+
- That's it! (tkinter included)

## Adding a New Connector

Drop a `.json` file into the `connectors/` folder — it appears in the dropdown automatically, no code changes needed.

```json
{
  "name": "MyConnector",
  "description": "My API connector",
  "request_patterns": [
    {
      "regex": "/request:\\s*(?P<endpoint>[^:\\s]+):\\s*(?P<error_type>Recoverable fail|Unrecoverable fail)...",
      "has_json_body": true,
      "body_fields": ["message", "errorMessages"]
    }
  ],
  "path_pattern": "Failed to get folder content:\\s*(/[^.]+?)(?:\\. Cause:|$)",
  "path_depth": 2,
  "report": {
    "title": "MY CONNECTOR FAILURE REPORT",
    "requests_section": "REQUEST FAILURE SUMMARY",
    "paths_section": "PATH FAILURE SUMMARY"
  }
}
```

**This tool is used daily at Keepit. Fork it, use it, improve it!**
