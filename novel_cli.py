import os
import sys
import click
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 将 .claude/scripts 加入环境变量，以便能调用其原有的 data_modules
project_root = os.path.dirname(os.path.abspath(__file__))
scripts_path = os.path.join(project_root, ".claude", "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from llm_manager import LLMManager

@click.group()
def cli():
    """Webnovel Writer - AI 小说全自动创作引擎 (Python Refactored)"""
    pass

@cli.command()
@click.option('--msg', default="Hello", help="测试发给大模型的测试消息")
def ping(msg):
    """测试大模型连通性"""
    click.echo(f"正在通过 LLMManager 连接大模型，发送: {msg}")
    llm = LLMManager()
    
    try:
        response_text = llm.chat(msg)
        click.secho("\n✅ [成功] 收到模型回复：", fg="green", bold=True)
        click.echo(response_text)
    except Exception as e:
        click.secho(f"\n❌ [失败] 请求抛出异常：\n{e}", fg="red", bold=True)


@cli.command()
def init():
    """初始化一个全新的小说项目 (交互式设定)"""
    from init_pipeline import run_init_pipeline
    run_init_pipeline()

@cli.command()
def plan():
    """根据项目现有世界观和总纲，推演卷内详细章纲"""
    from plan_pipeline import run_plan_pipeline
    run_plan_pipeline()

@cli.command()
def write():
    """执行自动化正文生成 (Draft -> Review -> Polish)"""
    from write_pipeline import run_write_pipeline
    run_write_pipeline()

if __name__ == '__main__':
    cli()
