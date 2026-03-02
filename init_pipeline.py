import os
import sys
import json
import click
from llm_manager import LLMManager

# 确保能加载内部 scripts
project_root = os.path.dirname(os.path.abspath(__file__))
scripts_path = os.path.join(project_root, ".claude", "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# 因为原项目使用 python 脚本执行，我们可以直接 import
from init_project import init_project

def run_init_pipeline():
    """执行交互式的小说初始化流程"""
    click.secho("\n=== 🔮 欢迎使用 Webnovel Writer (Python 重构版) ===", fg="blue", bold=True)
    click.echo("接下来我们将通过几个核心问题，确立您的小说世界与大纲基调。\n")
    
    # 模拟原来的 Wave 1-4 收集
    title = click.prompt("1. 书名是？(为空则随机生成)", default="未命名计划")
    genre = click.prompt("2. 题材类别是？(如: 修仙/系统流/都市异能/科幻)", default="都市异能")
    target_words = click.prompt("3. 目标完成总字数？(例如: 1000000)", default="1000000")
    one_liner = click.prompt("4. 请用一句话描述你的故事？", default="")
    
    click.secho("\n--- 正在请求 AI 顾问为您填充细节参数 ---", fg="yellow")
    
    # 在重构版中，我们通过 LLM 一次性将基础架构发给模型，让他返回包含丰富设定的 JSON
    llm = LLMManager()
    
    system_prompt = """
    你是一个骨灰级网络小说主编和架构师。
    用户提供了一个小说的【书名】、【题材】、【目标】和【一句话简介】。
    请你根据网文市场规律，帮他把剩下需要的数十个世界观设定、主角人设、金手指设定、反派分层全部填充丰满。
    必须返回一个纯合法的 JSON 字符串，不要有 markdown 语法，字段如下：
    {
      "protagonist_name": "林风",
      "protagonist_archetype": "杀伐果断/智商在线",
      "protagonist_desire": "查清当年灭门真相",
      "protagonist_flaw": "为了复仇不择手段，共情能力低",
      "golden_finger_name": "万物解析面板",
      "golden_finger_type": "系统面板",
      "golden_finger_style": "无机质提示音，绝对理智",
      "core_selling_points": "从底层一路平推，毫无憋屈感的高效升级",
      "world_scale": "现代都市背后的高武里世界",
      "power_system_type": "超凡异能体系",
      "antagonist_tiers": "街区帮派 -> 财阀集团 -> 幕后隐世家族"
    }
    """
    
    user_prompt = f"书名：{title}\n题材：{genre}\n一句话故事：{one_liner}"
    
    response = ""
    try:
        response = llm.chat(prompt=user_prompt, system_prompt=system_prompt)
        
        # 使用正则提取 JSON 内容，增强容错
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
        else:
            clean_json = response
            
        settings = json.loads(clean_json.strip())
        click.secho("\n✅ AI 设定推演完成！\n", fg="green")
        for k, v in settings.items():
            click.echo(f"  - {k}: {v}")
            
    except Exception as e:
        click.secho(f"解析 AI 设定失败，将使用默认兜底参数: {e}", fg="red")
        click.secho(f"--- 原始返回文本 ---\n{response}\n-------------------", fg="yellow")
        settings = {
            "protagonist_name": "主角",
            "golden_finger_name": "未知金手指"
        }
        
    click.secho("\n--- 正在生成本地项目骨架与数据库 ---", fg="cyan")
    
    # 构建传给被调脚本的 args 类
    class Args:
        pass
    args = Args()
    args.project_dir = title.replace(" ", "-") if title != "未命名计划" else "proj-novel"
    args.title = title
    args.genre = genre
    args.target_words = int(target_words)
    args.target_chapters = args.target_words // 3000
    
    # 将字典平铺到 args 对象
    for k, v in settings.items():
        setattr(args, k, v)
        
    # 其他必定默认的参数（简化填补原脚本的所有长尾参数）
    default_attrs = [
        ("protagonist_structure", "单主角"), ("heroine_config", "无"), ("heroine_names", ""),
        ("heroine_role", ""), ("co_protagonists", ""), ("co_protagonist_roles", ""),
        ("factions", "未知"), ("social_class", "分明"), ("resource_distribution", "集中"),
        ("gf_visibility", "仅自己可见"), ("gf_irreversible_cost", "无"), ("currency_system", "灵石"),
        ("currency_exchange", "1:100"), ("sect_hierarchy", "外门内门真传"), ("cultivation_chain", "一至九阶"),
        ("cultivation_subtiers", "初中后巅峰"), ("antagonist_level", "与主角持平或高一阶"),
        ("target_reader", "网文老白"), ("platform", "全平台")
    ]
    for k, v in default_attrs:
        if not hasattr(args, k):
            setattr(args, k, v)
            
    # 调用底层的初始化脚本
    try:
        import inspect
        sig = inspect.signature(init_project)
        valid_keys = set(sig.parameters.keys())
        
        kwargs = vars(args).copy()
        project_dir = kwargs.pop('project_dir')
        title = kwargs.pop('title')
        genre = kwargs.pop('genre')
        
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        
        init_project(project_dir, title, genre, **filtered_kwargs)
        click.secho(f"\n🎉 项目初始化成功！目录建立在: ./{args.project_dir}", fg="green", bold=True)
    except Exception as e:
        import traceback
        click.secho(f"\n❌ 初始化脚本执行失败: {e}\n{traceback.format_exc()}", fg="red", bold=True)
