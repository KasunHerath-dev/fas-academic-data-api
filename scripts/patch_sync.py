import sys
import os
sys.path.append(os.getcwd())

with open("scripts/run_academic_data_sync.py", "r") as f:
    content = f.read()

summary_code = """
    logger.info(f"Sync complete. Status: {final_status}")
    logger.info(f"Checked: {sync_run.documents_checked}, Changed: {sync_run.documents_changed}, Processed: {sync_run.documents_processed}, Skipped: {sync_run.documents_skipped}, Failed: {sync_run.documents_failed}")
    
    # Write summary for GitHub Actions
    summary = f\"\"\"
### Sync Run: {final_status.upper()}
- **Documents Discovered/Checked:** {sync_run.documents_checked}
- **Documents Changed:** {sync_run.documents_changed}
- **Documents Skipped:** {sync_run.documents_skipped}
- **Successfully Processed:** {sync_run.documents_processed}
- **Parse/Validation Failures:** {sync_run.documents_failed}
\"\"\"
    if error_summary:
        summary += f"\\n**Error Summary:** {error_summary}\\n"
        
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a") as sf:
                sf.write(summary)
        except:
            pass
"""

content = content.replace(
    'logger.info(f"Sync complete. Status: {final_status}")\n    logger.info(f"Checked: {sync_run.documents_checked}, Changed: {sync_run.documents_changed}, Processed: {sync_run.documents_processed}, Skipped: {sync_run.documents_skipped}, Failed: {sync_run.documents_failed}")',
    summary_code
)

with open("scripts/run_academic_data_sync.py", "w") as f:
    f.write(content)

# Patch the github actions workflow
with open(".github/workflows/academic-data-sync.yml", "r") as f:
    workflow = f.read()

workflow = workflow.replace(
    'echo "## Synchronization Summary" >> $GITHUB_STEP_SUMMARY\n          echo "\\`\\`\\`" >> $GITHUB_STEP_SUMMARY\n          tail -n 10 sync_output.log >> $GITHUB_STEP_SUMMARY\n          echo "\\`\\`\\`" >> $GITHUB_STEP_SUMMARY',
    '# Summary is now appended directly by run_academic_data_sync.py'
)

with open(".github/workflows/academic-data-sync.yml", "w") as f:
    f.write(workflow)
