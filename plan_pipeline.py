import os
import sys
import json
import click
from pathlib import Path
from llm_manager import LLMManager

def run_plan_pipeline():
    """执行交互式的小说分卷大纲推演流程"""
    click.secho("\n=== 🗺️ 欢迎使用 Webnovel Writer - 分卷大纲引擎 ===", fg="blue", bold=True)
    
    # 查找当前目录下的 state.json
    project_root = os.getcwd()
    state_file = os.path.join(project_root, ".webnovel", "state.json")
    outline_master_file = os.path.join(project_root, "大纲", "总纲.md")
    
    if not os.path.exists(state_file) or not os.path.exists(outline_master_file):
        click.secho("❌ 错误：当前目录下未检测到完整的项目结构（缺失 state.json 或 总纲.md）。请先运行 init 或者 cd 到小说根目录。", fg="red")
        return
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    with open(outline_master_file, 'r', encoding='utf-8') as f:
        master_outline = f.read()
        
    title = state.get("project_info", {}).get("title", "未知作品")
    
    click.echo(f"已加载项目：【{title}】")
    
    volume_num = click.prompt("👉 请输入你要推演大纲的【卷号】 (例如: 1)", type=int, default=1)
    chapters_per_volume = click.prompt("👉 本卷大概多少章？", type=int, default=50)
    
    start_ch = (volume_num - 1) * chapters_per_volume + 1
    end_ch = volume_num * chapters_per_volume
    
    click.secho(f"\n--- 正在请求 AI 顾问为您推演 第 {volume_num} 卷 ({start_ch}-{end_ch}章) 的详细章纲 ---", fg="yellow")
    click.echo("由于需要极强的逻辑连贯性，该步骤预估耗时 30~60 秒，请耐心等待...")
    
    # 提取设定的基础上下文 (模拟原版 L1/L2 加载)
    ctx_parts = []
    settings_dir = os.path.join(project_root, "设定集")
    if os.path.exists(settings_dir):
        for fname in ["世界观.md", "力量体系.md", "主角卡.md", "金手指设计.md", "反派设计.md"]:
            fpath = os.path.join(settings_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    ctx_parts.append(f"====== {fname} ======\n{f.read()}")
                    
    context_str = "\n".join(ctx_parts)
    
    llm = LLMManager()
    
    system_prompt = f"""
    你是一个顶级的网文主编和剧情推演大师。
    现在你需要为小说《{title}》的 第 {volume_num} 卷 编写一版超级硬核的“分章大纲”。
    
    本卷章节跨度：第 {start_ch} 章 到 第 {end_ch} 章。
    
    你需要严格遵循以下输出格式规划本卷每一章的剧情：
    
    # 第 {volume_num} 卷：[本卷核心卷名]
    > 核心冲突：...
    > 卷末高潮：...
    
    ## 详细章纲
    （请以此格式输出每一章）
    ### 第 N 章：[章节名]
    - 目标: [20字以内，主角这章要做什么]
    - 爽点: [类型] - [30字以内，比如：打脸反派/获得宝物]
    - Strand: [Quest(主线) 或 Fire(情感) 或 Constellation(解谜)]
    - 反派层级: [无/小/中/大]
    - 钩子: [类型] - [30字结尾悬念，比如：危机钩 - 师妹突然遇刺]
    - 剧情概要: [100字左右详细剧情说明]
    
    请直接输出 Markdown 格式的细纲。请确保这 {chapters_per_volume} 章剧情连贯，一气呵成，并导向卷末的高潮。
    如果章节太多，你可以将其分为几个阶段（比如前期铺垫、中期发育、后期冲突）来组织。
    """
    
    user_prompt = f"项目总大纲如下：\n{master_outline}\n\n具体设定参考如下：\n{context_str}\n\n请开始编写 第 {volume_num} 卷 详细章纲："
    
    try:
        response = llm.chat(prompt=user_prompt, system_prompt=system_prompt, max_tokens=8192)
        
        output_file = os.path.join(project_root, "大纲", f"第{volume_num}卷-详细大纲.md")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.strip())
            
        click.secho(f"\n✅ 第 {volume_num} 卷详细大纲推演完成！", fg="green", bold=True)
        click.echo(f"文件已保存至: {output_file}")
        
    except Exception as e:
        import traceback
        click.secho(f"\n❌ 推演大纲失败: {e}\n{traceback.format_exc()}", fg="red", bold=True)
