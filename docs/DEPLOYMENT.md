# Deployment and submission

## Local Mac
1. Extract the ZIP completely; do not run files from inside an archive preview.
2. Read START_HERE.html and README.md.
3. Install Python 3.12 if needed. Run Setup_Mac.command, then Launch_Mac.command.
4. If macOS opens a command file as text or denies executable permission, use Terminal in the project folder: `bash Setup_Mac.command` and `bash Launch_Mac.command`. Do not bypass browser certificate/security warnings.
5. Stop the running app using Ctrl+C in Terminal.

## GitHub
Create a new repository in your own account. Upload source, requirements, configuration, docs, tests, and `data/processed/`. The archive includes raw source pages for reproducibility, but .gitignore deliberately excludes data/raw from routine git additions. Preserve that frozen snapshot in an appropriate versioned data location and document the retrieval/regeneration route. Never upload .venv or secrets. This bundle has not created or modified a GitHub repository.

## Streamlit Community Cloud
Connect your repository, select app.py, and select Python 3.12. Runtime charts use bundled processed JSON/CSV files and do not require a live OpenAlex API key. Complete all checks in QA.md on the published URL. Record any error, response time, tested viewport, and unresolved accessibility issue.

## Blackboard
Submit the live URL, repository link, and accompanying narrative/materials requested by the instructor. Do not claim that a local or AppTest pass proves live deployment or mobile accessibility. Review the actual course AI-use policy and make an accurate disclosure.
