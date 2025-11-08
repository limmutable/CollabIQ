# Key Code Snippets - User Story 4 Implementation

## 1. Cost Calculation (CostTracker)

```python
def _calculate_cost(
    self, provider_name: str, input_tokens: int, output_tokens: int
) -> float:
    """Calculate cost for a single API call.
    
    Formula:
        cost = (input_tokens / 1_000_000) * input_token_price
             + (output_tokens / 1_000_000) * output_token_price
    """
    if provider_name not in self.provider_configs:
        return 0.0
    
    config = self.provider_configs[provider_name]
    
    input_cost = (input_tokens / 1_000_000) * config.input_token_price
    output_cost = (output_tokens / 1_000_000) * config.output_token_price
    
    return input_cost + output_cost
```

## 2. Usage Recording (CostTracker)

```python
def record_usage(
    self,
    provider_name: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """Record API usage and calculate cost."""
    metrics = self.get_metrics(provider_name)
    
    # Update counters
    metrics.total_api_calls += 1
    metrics.total_input_tokens += input_tokens
    metrics.total_output_tokens += output_tokens
    metrics.total_tokens = metrics.total_input_tokens + metrics.total_output_tokens
    
    # Calculate cost for this call
    call_cost = self._calculate_cost(provider_name, input_tokens, output_tokens)
    metrics.total_cost_usd += call_cost
    
    # Update average cost per email
    if metrics.total_api_calls > 0:
        metrics.average_cost_per_email = (
            metrics.total_cost_usd / metrics.total_api_calls
        )
    
    # Update timestamp and persist
    metrics.last_updated = datetime.now(timezone.utc)
    self._save_metrics()
```

## 3. CLI Status Display (Basic)

```python
def _display_basic_status(provider_status: dict):
    """Display basic provider health status."""
    console.print("\n[bold cyan]LLM Provider Health Status[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Provider", style="cyan", width=12)
    table.add_column("Health", justify="center", width=10)
    table.add_column("Circuit", justify="center", width=10)
    table.add_column("Success Rate", justify="right", width=12)
    table.add_column("Errors", justify="right", width=8)
    table.add_column("Avg Response", justify="right", width=12)
    table.add_column("Last Success", justify="center", width=16)
    table.add_column("Last Failure", justify="center", width=16)
    
    for provider_name, status in provider_status.items():
        # Color-coded health status
        health_color = "green" if status.health_status == "healthy" else "red"
        health_display = f"[{health_color}]{status.health_status.upper()}[/{health_color}]"
        
        # Color-coded circuit breaker state
        cb_state = status.circuit_breaker_state.upper()
        if cb_state == "CLOSED":
            cb_display = f"[green]{cb_state}[/green]"
        elif cb_state == "OPEN":
            cb_display = f"[red]{cb_state}[/red]"
        else:  # HALF_OPEN
            cb_display = f"[yellow]{cb_state}[/yellow]"
        
        table.add_row(
            provider_name.title(),
            health_display,
            cb_display,
            f"{status.success_rate:.1%}",
            str(error_count),
            f"{status.average_response_time_ms:.0f}ms",
            _format_timestamp(status.last_success),
            _format_timestamp(status.last_failure),
        )
    
    console.print(table)
```

## 4. CLI Status Display (Detailed - Cost Metrics)

```python
# Cost Metrics Table
if orchestrator.cost_tracker:
    console.print("\n[bold]Cost Metrics[/bold]\n")
    cost_table = Table(show_header=True, header_style="bold magenta")
    cost_table.add_column("Provider", style="cyan", width=12)
    cost_table.add_column("API Calls", justify="right", width=10)
    cost_table.add_column("Input Tokens", justify="right", width=14)
    cost_table.add_column("Output Tokens", justify="right", width=14)
    cost_table.add_column("Total Cost", justify="right", width=12)
    cost_table.add_column("Cost/Email", justify="right", width=12)
    
    cost_metrics = orchestrator.cost_tracker.get_all_metrics()
    
    for provider_name in provider_status.keys():
        metrics = cost_metrics.get(provider_name)
        if metrics:
            cost_table.add_row(
                provider_name.title(),
                str(metrics.total_api_calls),
                f"{metrics.total_input_tokens:,}",
                f"{metrics.total_output_tokens:,}",
                f"${metrics.total_cost_usd:.4f}",
                f"${metrics.average_cost_per_email:.6f}",
            )
    
    console.print(cost_table)
```

## 5. Timestamp Formatting

```python
def _format_timestamp(dt: datetime) -> str:
    """Format datetime for display (relative time)."""
    if dt is None:
        return "Never"
    
    # Make timezone aware if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(dt.tzinfo)
    delta = now - dt
    
    if delta.total_seconds() < 60:
        return "Just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes}m ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(delta.total_seconds() / 86400)
        return f"{days}d ago"
```

## 6. Orchestrator Integration

```python
# In LLMOrchestrator.__init__()
def __init__(
    self,
    providers: dict[str, LLMProvider],
    config: OrchestrationConfig,
    health_tracker: "HealthTracker",
    cost_tracker: Optional["CostTracker"] = None,  # Added
):
    self.providers = providers
    self.config = config
    self.health_tracker = health_tracker
    self.cost_tracker = cost_tracker  # Store cost tracker

# In LLMOrchestrator.from_config()
cost_tracker = CostTracker(
    data_dir=data_dir,
    provider_configs=provider_configs,
)

return cls(
    providers=providers,
    config=config,
    health_tracker=health_tracker,
    cost_tracker=cost_tracker,  # Pass to constructor
)
```

## 7. Atomic File Writes (Persistence)

```python
def _save_metrics(self) -> None:
    """Save cost metrics to JSON file using atomic write."""
    # Convert metrics to JSON-serializable dict
    data = {}
    for provider_name, metrics in self.metrics.items():
        metrics_dict = metrics.model_dump()
        
        # Convert datetime to ISO format
        if metrics_dict.get("last_updated"):
            metrics_dict["last_updated"] = metrics_dict["last_updated"].isoformat()
        
        data[provider_name] = metrics_dict
    
    # Atomic write: temp file + rename
    temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")
    
    try:
        with os.fdopen(temp_fd, "w") as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename (prevents corruption)
        shutil.move(temp_path, self.metrics_file)
    
    except Exception as e:
        # Clean up temp file on error
        if Path(temp_path).exists():
            Path(temp_path).unlink()
        logger.error(f"Failed to save cost metrics: {e}")
        raise
```

## 8. Test Example (Cost Calculation)

```python
def test_record_usage_calculates_cost_correctly(temp_data_dir, provider_configs):
    """Test cost calculation using provider-specific pricing.
    
    Claude pricing: $3/1M input, $15/1M output
    Usage: 1,000,000 input + 500,000 output
    Expected cost: (1M / 1M) * $3 + (500K / 1M) * $15 = $3 + $7.50 = $10.50
    """
    tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)
    
    tracker.record_usage("claude", input_tokens=1_000_000, output_tokens=500_000)
    
    metrics = tracker.get_metrics("claude")
    assert metrics.total_cost_usd == pytest.approx(10.50, rel=1e-4)
```

## 9. Provider Config with Pricing

```python
provider_configs = {
    "claude": ProviderConfig(
        provider_name="claude",
        display_name="Claude Sonnet 4.5",
        model_id="claude-sonnet-4-5-20250929",
        api_key_env_var="ANTHROPIC_API_KEY",
        enabled=True,
        priority=2,
        timeout_seconds=60.0,
        max_retries=3,
        input_token_price=3.0,   # $3 per 1M input tokens
        output_token_price=15.0,  # $15 per 1M output tokens
    ),
}
```

## 10. CLI Command Structure

```python
@app.command()
def status(
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed cost metrics and orchestration info",
    ),
):
    """View LLM provider health status and metrics."""
    try:
        # Create orchestrator with default config
        config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=["gemini", "claude", "openai"],
        )
        orchestrator = LLMOrchestrator.from_config(config)
        
        # Get provider status
        provider_status = orchestrator.get_provider_status()
        
        # Display based on detail level
        if detailed:
            _display_detailed_status(orchestrator, provider_status)
        else:
            _display_basic_status(provider_status)
    
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        raise typer.Exit(1)
```
