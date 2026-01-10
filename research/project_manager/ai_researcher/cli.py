"""
命令行接口
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.agent import ResearchAgent
from .templates.manager import TemplateManager

console = Console()


@click.group()
def cli():
    """AI科研助手 - 智能实验方案生成和管理系统"""
    pass


@cli.command()
@click.option("--model-provider", default="openai", help="模型提供商")
@click.option("--model-name", default="gpt-4", help="模型名称")
@click.option("--ragflow-endpoint", default="http://localhost:9380", help="RAGFlow地址")
@click.argument("objective")
def create(model_provider, model_name, ragflow_endpoint, objective):
    """创建新的实验方案"""
    console.print(Panel.fit(f"[bold blue]AI科研助手[/bold blue]\n正在生成实验方案..."))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("初始化助手...", total=None)
            agent = ResearchAgent(
                model_provider=model_provider,
                model_name=model_name,
                ragflow_endpoint=ragflow_endpoint
            )

            task = progress.add_task("检索知识库...", total=None)
            plan = agent.generate_experiment_plan(objective)

            # 显示结果
            console.print("\n[bold green]✓ 实验方案生成成功![/bold green]\n")

            table = Table(title="实验方案信息")
            table.add_column("字段", style="cyan")
            table.add_column("内容", style="white")

            table.add_row("实验ID", plan.get("id", ""))
            table.add_row("实验标题", plan.get("title", ""))
            table.add_row("状态", plan.get("status", "planned"))

            console.print(table)

            if click.confirm("是否查看详细方案?"):
                console.print("\n" + Panel(json.dumps(plan, indent=2, ensure_ascii=False)))

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("experiment_id")
def status(experiment_id):
    """查看实验状态"""
    try:
        agent = ResearchAgent()
        exp = agent.get_experiment_status(experiment_id)

        if not exp:
            console.print(f"[red]实验 {experiment_id} 不存在[/red]")
            return

        console.print(Panel.fit(f"实验 [bold]{experiment_id}[/bold]"))

        table = Table()
        table.add_column("字段", style="cyan")
        table.add_column("内容", style="white")

        table.add_row("标题", exp.get("title", ""))
        table.add_row("目标", exp.get("objective", ""))
        table.add_row("状态", f"[bold]{exp.get('status', 'unknown')}[/bold]")
        table.add_row("创建时间", exp.get("created_at", ""))
        table.add_row("更新时间", exp.get("updated_at", ""))

        console.print(table)

        # 显示进度历史
        progress = agent.experiments.get_progress_history(experiment_id)
        if progress:
            console.print("\n[bold]进度历史:[/bold]")
            for p in progress[-5:]:  # 显示最近5条
                console.print(f"  • {p['timestamp']}: {p['status']} - {p.get('notes', '')}")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.option("--status", help="过滤状态")
def list(status):
    """列出所有实验"""
    try:
        agent = ResearchAgent()
        experiments = agent.list_experiments(status=status)

        if not experiments:
            console.print("[yellow]暂无实验记录[/yellow]")
            return

        table = Table(title="实验列表")
        table.add_column("ID", style="cyan")
        table.add_column("标题", style="white")
        table.add_column("状态", style="green")
        table.add_column("创建时间", style="blue")

        for exp in experiments:
            status_color = {
                "planned": "yellow",
                "in_progress": "blue",
                "completed": "green",
                "failed": "red"
            }.get(exp["status"], "white")

            table.add_row(
                exp["id"],
                exp["title"],
                f"[{status_color}]{exp['status']}[/{status_color}]",
                exp["created_at"][:19]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("experiment_id")
@click.option("--data-file", help="数据文件路径")
def analyze(experiment_id, data_file):
    """分析实验结果"""
    console.print(f"[bold blue]分析实验 {experiment_id} 的结果...[/bold blue]")

    try:
        agent = ResearchAgent()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("分析数据...", total=None)

            if data_file:
                analysis = agent.analyze_results(
                    experiment_id=experiment_id,
                    data_file=data_file
                )
            else:
                console.print("[yellow]请提供数据文件路径 (--data-file)[/yellow]")
                return

            task = progress.add_task("生成报告...", total=None)
            console.print("\n[bold green]✓ 分析完成![/bold green]\n")

            # 显示数据概览
            if "data_summary" in analysis:
                console.print(Panel("数据概览", analysis["data_summary"]["shape"]))

            # 显示AI解读
            if "ai_interpretation" in analysis:
                console.print("\n[bold]AI解读:[/bold]")
                interpretation = analysis["ai_interpretation"]
                if "text" in interpretation:
                    console.print(interpretation["text"])

            # 显示图表文件
            if "visualizations" in analysis and analysis["visualizations"]:
                console.print("\n[bold]生成的图表:[/bold]")
                for chart in analysis["visualizations"]:
                    console.print(f"  • {chart}")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("experiment_id")
@click.option("--format", default="json", help="导出格式 (json/yaml)")
def export(experiment_id, format):
    """导出实验方案"""
    try:
        agent = ResearchAgent()
        content = agent.export_experiment(experiment_id, format=format)

        if not content:
            console.print(f"[red]实验 {experiment_id} 不存在[/red]")
            return

        output_file = f"{experiment_id}.{format}"
        Path(output_file).write_text(content, encoding="utf-8")

        console.print(f"[green]✓ 已导出到 {output_file}[/green]")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
def templates():
    """列出可用模板"""
    try:
        manager = TemplateManager()
        templates = manager.list_templates()

        table = Table(title="可用模板")
        table.add_column("名称", style="cyan")
        table.add_column("描述", style="white")

        for name, desc in templates.items():
            table.add_row(name, desc)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.option("--provider", default="openai", help="模型提供商")
def init(provider):
    """初始化系统"""
    console.print("[bold blue]初始化AI科研助手...[/bold blue]\n")

    # 创建必要目录
    dirs = ["templates", "results/charts", "experiments"]
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        console.print(f"✓ 创建目录: {dir_name}")

    # 创建配置目录
    Path("config").mkdir(exist_ok=True)
    console.print("✓ 创建目录: config")

    console.print("\n[bold green]初始化完成![/bold green]")
    console.print("\n请使用 'config' 命令管理模型配置")


# ==================== 模型配置管理命令 ====================

@cli.group()
def config():
    """模型配置管理"""
    pass


# ==================== API密钥管理命令 ====================

@config.group()
def keys():
    """API密钥管理"""
    pass


@keys.command()
def setup():
    """交互式设置所有API密钥"""
    from .secrets_manager import get_secrets_manager

    try:
        secrets_manager = get_secrets_manager()
        secrets_manager.setup_interactive()
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@keys.command()
def status():
    """显示API密钥状态"""
    from .secrets_manager import check_api_keys

    try:
        status = check_api_keys()

        table = Table(title="API密钥状态")
        table.add_column("提供商", style="cyan")
        table.add_column("状态", style="white")

        for provider, has_key in status.items():
            status_text = "[green]✓ 已配置[/green]" if has_key else "[red]✗ 未配置[/red]"
            table.add_row(provider.upper(), status_text)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@keys.command()
@click.argument("provider")
@click.option("--key", prompt=True, help="API密钥")
def set(provider, key):
    """设置API密钥"""
    from .secrets_manager import set_api_key

    try:
        set_api_key(provider.lower(), key)
        console.print(f"[green]✓ {provider.upper()} API密钥已保存[/green]")
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@keys.command()
@click.argument("provider")
def delete(provider):
    """删除API密钥"""
    from .secrets_manager import get_secrets_manager

    try:
        secrets_manager = get_secrets_manager()
        if click.confirm(f"确认删除 {provider.upper()} API密钥?"):
            secrets_manager.delete_api_key(provider.lower())
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
@click.option("--name", prompt=True, help="配置名称")
@click.option("--provider", prompt=True, help="提供商 (OpenAI/Gemini/Anthropic/Custom)")
@click.option("--endpoint", help="API Endpoint (可选)")
@click.option("--api-type", default="chat", help="API类型 (chat/response/reasoning)")
@click.option("--api-key", prompt=True, help="API密钥")
@click.option("--model-name", prompt=True, help="模型名称")
@click.option("--temperature", default=0.7, help="温度参数")
@click.option("--max-tokens", default=4000, help="最大token数")
@click.option("--activate/--no-activate", default=True, help="是否激活此配置")
def add(name, provider, endpoint, api_type, api_key, model_name, temperature, max_tokens, activate):
    """添加模型配置"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()

        success = manager.add_model_config(
            name=name,
            provider=provider,
            endpoint=endpoint,
            api_type=api_type,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            is_active=activate
        )

        if success:
            console.print(f"[green]✓ 模型配置添加成功: {name}[/green]")

            if activate:
                console.print(f"[yellow]ℹ️  已激活配置: {name}[/yellow]")
        else:
            console.print("[red]✗ 添加配置失败[/red]")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
def list():
    """列出所有模型配置"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()
        configs = manager.list_model_configs()

        if not configs:
            console.print("[yellow]暂无模型配置[/yellow]")
            console.print("使用 'config add' 添加配置")
            return

        table = Table(title="模型配置列表")
        table.add_column("名称", style="cyan")
        table.add_column("提供商", style="green")
        table.add_column("模型", style="blue")
        table.add_column("Endpoint", style="yellow")
        table.add_column("状态", style="white")

        for config in configs:
            status = "✓ 激活" if config.get('is_active') else "○ 未激活"
            endpoint = config.get('endpoint', '') or '-'

            table.add_row(
                config['name'],
                config['provider'],
                config['model_name'],
                endpoint,
                status
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
@click.argument("name")
def show(name):
    """显示配置详情"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()
        config = manager.get_model_config(name)

        if not config:
            console.print(f"[red]配置不存在: {name}[/red]")
            return

        console.print(Panel.fit(f"[bold]配置详情: {name}[/bold]"))

        table = Table(show_header=False, box=None)
        table.add_column("字段", style="cyan", width=20)
        table.add_column("值", style="white")

        # 隐藏API密钥
        masked_api_key = config.get('api_key', '')
        if masked_api_key:
            masked_api_key = '*' * (len(masked_api_key) - 4) + masked_api_key[-4:]

        fields = [
            ("名称", config['name']),
            ("提供商", config['provider']),
            ("模型", config['model_name']),
            ("Endpoint", config.get('endpoint', '-')),
            ("API类型", config.get('api_type', '-')),
            ("API密钥", masked_api_key),
            ("温度", str(config.get('temperature', '-'))),
            ("最大Token", str(config.get('max_tokens', '-'))),
            ("状态", "激活" if config.get('is_active') else "未激活"),
            ("创建时间", config.get('created_at', '-')),
        ]

        for key, value in fields:
            table.add_row(key, str(value))

        console.print(table)

        # 显示额外参数
        if config.get('extra_params'):
            console.print("\n[bold]额外参数:[/bold]")
            console.print(json.dumps(config['extra_params'], indent=2, ensure_ascii=False))

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
@click.argument("name")
def activate(name):
    """激活配置"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()
        success = manager.activate_config(name)

        if success:
            console.print(f"[green]✓ 已激活配置: {name}[/green]")
        else:
            console.print(f"[red]✗ 激活失败，配置不存在: {name}[/red]")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
@click.argument("name")
def delete(name):
    """删除配置"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()

        if click.confirm(f"确认删除配置 '{name}' ?"):
            success = manager.delete_model_config(name)

            if success:
                console.print(f"[green]✓ 已删除配置: {name}[/green]")
            else:
                console.print(f"[red]✗ 删除失败，配置不存在: {name}[/red]")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
@click.argument("name")
def test(name):
    """测试配置连接"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()
        result = manager.test_connection(name)

        if result['success']:
            console.print("[green]✓ 连接测试成功[/green]")
            console.print("\n[bold]配置信息:[/bold]")
            config_info = result['config']

            table = Table(show_header=False, box=None)
            table.add_column("字段", style="cyan", width=15)
            table.add_column("值", style="white")

            for key, value in config_info.items():
                table.add_row(key, str(value))

            console.print(table)
        else:
            console.print(f"[red]✗ 连接测试失败: {result.get('error')}[/red]")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


@config.command()
def providers():
    """显示支持的提供商"""
    try:
        from .models.config_manager import ModelConfigManager

        manager = ModelConfigManager()
        providers = manager.get_provider_configs()

        table = Table(title="支持的模型提供商")
        table.add_column("提供商", style="cyan")
        table.add_column("默认Endpoint", style="green")
        table.add_column("支持模型", style="blue")
        table.add_column("描述", style="yellow")

        for provider in providers:
            table.add_row(
                provider['provider_name'],
                provider['default_endpoint'] or '-',
                provider['supported_models'] or '-',
                provider['description'] or '-'
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.Abort()


if __name__ == "__main__":
    cli()
