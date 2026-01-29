# BRE Export MCP Server

An MCP (Model Context Protocol) server that provides tools for querying JSON datasets of GitHub repositories. The server enables Large Language Models to access repository information through structured queries and semantic search (RAG).

## Overview

This project provides:
- An **MCP server** that accepts JSON data uploads and exposes query tools
- A **chat client** (`chat.py`) that demonstrates the full workflow with OpenAI

The architecture is session-based: the client uploads JSON data to the server, which stores it in memory for the duration of the session.

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key

### Setup

```bash
git clone https://github.com/your-username/BRE-export-mcp.git
cd BRE-export-mcp
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key" > .env
```

## Usage

```bash
python chat.py <path-to-json-file>
```

Example:
```bash
python chat.py BettysResult_seismology_tools_doi_in_readme.json
```

## Available Tools

| Tool | Description |
|------|-------------|
| `upload_data` | Upload JSON data to initialize the session (called automatically) |
| `list_repos` | List repositories with pagination |
| `get_repo_details` | Get full details for a specific repository |
| `search_by_name` | Search by repository name |
| `filter_by_language` | Filter by programming language |
| `sort_by_stars` | Sort by GitHub stars |
| `sort_by_forks` | Sort by fork count |
| `get_repos_with_paper` | Get repositories with academic papers |
| `get_repos_with_citations` | Get cited repositories |
| `get_repos_by_date_range` | Filter by date |
| `semantic_search` | Natural language search (RAG) |
| `get_statistics` | Dataset statistics |
| `get_available_languages` | List programming languages |

## Data Format

The JSON file should be an array of repository objects:

```json
[
  {
    "name": "owner/repo-name",
    "url": "https://github.com/owner/repo-name",
    "description": "Short description",
    "stars": 123,
    "forks": 45,
    "readme": "Full README content...",
    "language": "Python",
    "mainPaper": {
      "doi": "10.1234/example",
      "title": "Paper Title",
      "citationsArray": ["10.1234/citing-paper"]
    }
  }
]
```

## Project Structure

```
BRE-export-mcp/
├── chat.py              # Main demo - interactive chat client
├── src/bre_mcp/
│   ├── server.py        # MCP server
│   ├── tools.py         # Tool implementations
│   ├── data_loader.py   # JSON data handling
│   ├── vector_store.py  # ChromaDB for semantic search
│   └── config.py        # Configuration
├── requirements.txt
├── .env                 # API keys
└── README.md
```

## License

MIT

# Example Interaction:

You: which of the repositories works with correlation of images?

🔧 Tool calls:
   → semantic_search({"query": "correlation of images", "limit": 10})

Assistant: Here are some repositories that work with the correlation of images, potentially relevant for seismology applications:

1. **[bickelmps/DIC_FFT_ETHZ](https://github.com/bickelmps/DIC_FFT_ETHZ)**  
   - **Description**: Digital Image Correlation using a Fast Fourier Transform approach.  
   - **Language**: MATLAB  
   - **Stars**: 42

2. **[ttsukianto/esip_julia_aws](https://github.com/ttsukianto/esip_julia_aws)**  
   - **Description**: Source code for a Julia-based AWS application to do seismic noise correlations.  
   - **Language**: Julia  
   - **Stars**: 1

These repositories focus on image correlation techniques and their applications, including seismic data analysis.

You: tell me more about the first one.

🔧 Tool calls:
   → get_repo_details({"name": "bickelmps/DIC_FFT_ETHZ"})

Assistant: The repository **[bickelmps/DIC_FFT_ETHZ](https://github.com/bickelmps/DIC_FFT_ETHZ)** is a MATLAB-based tool for Digital Image Correlation (DIC) using a Fast Fourier Transform (FFT) approach. Here's a detailed overview:

### Overview
- **Description**: The tool is designed for analyzing displacement in images, particularly useful for monitoring features like landslides and glaciers over time. It processes both single- and multi-channel, equal-dimension images and provides options for outputting geotiff information. The DIC tool is validated and calibrated for accurate results.
- **Functionality**: It quantifies displacement features and generates output data which includes 2D displacement maps and vectors, as well as GIS-ready formats (.tif and .txt). 

### Key Features
- **Image Pre-processing**: 
  - Wallis Filter for dynamic contrast enhancement
  - Sub-pixel image registration to improve accuracy 
- **Post-processing Capability**: 
  - Options to filter results based on RMSE, mean, and median techniques.

### Usage
1. **Input Images**: Users can place primary and secondary images in the "Input" folder.
2. **Customization**: Setup can be tailored through a script where users can modify parameters related to preprocessing, DIC, and post-processing.
3. **Execution**: Run the main script to collect results in the "Output" folder.

### Applications
The tool is currently employed by various research groups:
- Engineering Geology Group and Swiss Seismological Service at ETH Zurich
- Several universities and research institutes across Switzerland and Europe.

### Publication Reference
For users interested in the underlying methodologies, the tool has been referenced in the publication:
- **Bickel, V.T.; Manconi, A.; Amann, F.** (2018). "Quantitative Assessment of Digital Image Correlation Methods to Detect and Monitor Surface Displacements of Large Slope Instabilities." Remote Sens. 10, 865. [Read here](http://www.mdpi.com/2072-4292/10/6/865)

### Repository Statistics
- **Stars**: 42
- **Forks**: 19
- **Programming Language**: MATLAB
- **Last Updated**: October 29, 2024

For more details and to access the code, visit the [GitHub repository](https://github.com/bickelmps/DIC_FFT_ETHZ).

You: ...

# Known Issues:
The BRE Export currently seems to have an issue with the number of citations. As a consequence, the exampleInput files are not containing the citation data as expected. 

Since this is a BRE isse, we cannot fix it here.

As soon as BRE fixes this issue, this project will integrate it into a sort according to citations function.
