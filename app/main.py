import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from app.agents.orchestrator import AIOrchestrator
from app.utils.cost_tracker import cost_tracker
from app.utils.logger import logger

console = Console()

def main():
    orchestrator = AIOrchestrator()
    mode = "auto"
    
    console.print(Panel.fit(
        "[bold cyan]Multi-Model AI Chatbot System[/bold cyan]\n"
        "Available modes: [green]auto, ensemble, reflection[/green]\n"
        "Commands: [yellow]/model <name>, /mode <name>, /clear, /cost, /exit[/yellow]",
        title="Welcome"
    ))

    while True:
        try:
            user_input = console.input("[bold blue]User > [/bold blue]").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "/exit":
                break
                
            if user_input.startswith("/model"):
                parts = user_input.split()
                if len(parts) > 1:
                    orchestrator.current_model_id = parts[1]
                    console.print(f"[green]Switched to model: {parts[1]}[/green]")
                continue

            if user_input.startswith("/mode"):
                parts = user_input.split()
                if len(parts) > 1:
                    mode = parts[1]
                    console.print(f"[green]Switched to mode: {mode}[/green]")
                continue
                
            if user_input.lower() == "/clear":
                orchestrator.memory.clear()
                console.print("[yellow]Memory cleared.[/yellow]")
                continue
                
            if user_input.lower() == "/cost":
                summary = cost_tracker.get_summary()
                console.print(Panel(
                    f"Total Cost: [bold green]${summary['total_cost']:.4f}[/bold green]\n"
                    f"Breakdown: {summary['breakdown']}",
                    title="Cost Usage"
                ))
                continue

            with console.status("[bold green]Agent is thinking..."):
                response = orchestrator.chat(user_input, mode=mode)
            
            if "error" in response:
                console.print(f"[bold red]Error:[/bold red] {response['error']}")
            else:
                console.print(Panel(
                    Markdown(response["content"]),
                    title=f"[bold green]Assistant ({response['model']})[/bold green]",
                    subtitle=f"Tokens: {response['input_tokens']} in / {response['output_tokens']} out"
                ))

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    console.print("[bold yellow]Goodbye![/bold yellow]")

if __name__ == "__main__":
    main()
