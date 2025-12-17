"""
Command-line interface for the complexity analyzer.
"""

import os
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from .analyzer import RepositoryAnalyzer
from .models import ComplexityReport

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="complexity-analyzer",
    help="AI-powered code complexity analysis for GitHub repositories"
)
console = Console()


@app.command()
def analyze(
    repository_url: str = typer.Argument(
        ...,
        help="GitHub repository URL to analyze"
    ),
    provider: str = typer.Option(
        "openai",
        help="LLM provider: 'openai' or 'anthropic'"
    ),
    model: Optional[str] = typer.Option(
        None,
        help="Specific model name (e.g., 'gpt-4-turbo-preview')"
    ),
    max_files: int = typer.Option(
        50,
        help="Maximum number of files to analyze"
    ),
    output: Optional[str] = typer.Option(
        None,
        help="Output file path (JSON format)"
    ),
):
    """
    Analyze a GitHub repository for code complexity.
    
    Example:
        complexity-analyzer https://github.com/owner/repo
    """
    # Validate API keys
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY not found in environment[/red]")
        raise typer.Exit(1)
    
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]AI Complexity Analyzer[/bold cyan]")
    console.print(f"Repository: {repository_url}")
    console.print(f"Provider: {provider} (model: {model or 'default'})\n")
    
    # Initialize analyzer
    analyzer = RepositoryAnalyzer(
        llm_provider=provider,
        model=model,
        max_files=max_files
    )
    
    # Run analysis with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing repository...", total=None)
        
        try:
            report = analyzer.analyze(repository_url)
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"\n[red]Error during analysis: {e}[/red]")
            raise typer.Exit(1)
    
    # Display results
    _display_report(report)
    
    # Save to file if requested
    if output:
        _save_report(report, output)
        console.print(f"\n[green]Report saved to: {output}[/green]")


def _display_report(report: ComplexityReport):
    """Display analysis results in terminal."""
    console.print("\n[bold green]Analysis Complete![/bold green]\n")
    
    # Summary table
    summary = Table(title="Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="white")
    
    summary.add_row("Repository", report.repository_url)
    summary.add_row("Files Analyzed", str(len(report.analyzed_files)))
    summary.add_row("Average Complexity", f"{report.score:.2f}/100")
    summary.add_row("Top File", report.top_file)
    
    console.print(summary)
    
    # Top 5 most complex files
    console.print("\n[bold]Top 5 Most Complex Files:[/bold]\n")
    
    sorted_files = sorted(
        report.analyzed_files,
        key=lambda x: x.total_score,
        reverse=True
    )[:5]
    
    files_table = Table()
    files_table.add_column("Rank", style="cyan", width=6)
    files_table.add_column("File", style="white")
    files_table.add_column("Score", justify="right", style="yellow")
    files_table.add_column("Cyclomatic", justify="right")
    files_table.add_column("Architectural", justify="right")
    files_table.add_column("Algorithmic", justify="right")
    
    for idx, file in enumerate(sorted_files, 1):
        files_table.add_row(
            f"#{idx}",
            file.file_path,
            f"{file.total_score:.1f}",
            f"{file.cyclomatic_complexity:.1f}",
            f"{file.architectural_complexity:.1f}",
            f"{file.algorithmic_complexity:.1f}"
        )
    
    console.print(files_table)
    
    # Top file details
    top = sorted_files[0]
    console.print(f"\n[bold]Most Complex File Analysis:[/bold] {top.file_path}\n")
    console.print(f"[dim]{top.reasoning}[/dim]\n")
    
    if top.design_patterns:
        console.print(f"[bold]Design Patterns Detected:[/bold] {', '.join(top.design_patterns)}")


def _save_report(report: ComplexityReport, output_path: str):
    """Save report to JSON file."""
    import json
    from pathlib import Path
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(report.model_dump(), f, indent=2)


@app.command()
def version():
    """Show version information."""
    console.print("[bold cyan]AI Complexity Analyzer v1.0.0[/bold cyan]")
    console.print("Powered by LangChain & OpenAI/Anthropic")


if __name__ == "__main__":
    app()
