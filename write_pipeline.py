import os
import sys
import json
import click
import re
from pathlib import Path
from llm_manager import LLMManager

def run_write_pipeline():
    """执行自动化正文生成 (Multi-Agent Workflow)"""
    click.secho("\n=== 🖋️ 欢迎使用 Webnovel Writer - 核心写作引擎 ===", fg="blue", bold=True)
    
    project_root = os.getcwd()
    state_file = os.path.join(project_root, ".webnovel", "state.json")
    
    if not os.path.exists(state_file):
        click.secho("❌ 错误：当前目录下未检测到完整的项目结构（缺失 state.json）。请输入项目根目录。", fg="red")
        return
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    title = state.get("project_info", {}).get("title", "未知作品")
    click.echo(f"已加载项目：【{title}】")
    
    volume_num = click.prompt("👉 请输入你要写作的【卷号】 (例如: 1)", type=int, default=1)
    
    # 查找卷大纲
    outline_file = os.path.join(project_root, "大纲", f"第{volume_num}卷-详细大纲.md")
    if not os.path.exists(outline_file):
        click.secho(f"❌ 错误：找不到第 {volume_num} 卷的大纲文件 ({outline_file})。请先使用 plan 命令生成大纲。", fg="red")
        return
        
    with open(outline_file, 'r', encoding='utf-8') as f:
        volume_outline = f.read()

    # 加载设定集
    ctx_parts = []
    settings_dir = os.path.join(project_root, "设定集")
    if os.path.exists(settings_dir):
        for fname in ["世界观.md", "力量体系.md", "主角卡.md", "金手指设计.md", "反派设计.md"]:
            fpath = os.path.join(settings_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    ctx_parts.append(f"====== {fname} ======\n{f.read()}")
    settings_context = "\n".join(ctx_parts)
    
    # 获取用户需要生成的起始章和数量
    current_chapter = state.get("progress", {}).get("current_chapter", 0)
    suggested_start = current_chapter + 1
    
    start_chapter = click.prompt(f"👉 请输入起始写作【章号】", type=int, default=suggested_start)
    write_count = click.prompt(f"👉 请输入本次连续生成的【章数】", type=int, default=1)
    
    llm = LLMManager()
    
    chapter_dir = os.path.join(project_root, "正文", f"第{volume_num}卷")
    os.makedirs(chapter_dir, exist_ok=True)
    
    for ch_idx in range(start_chapter, start_chapter + write_count):
        click.secho(f"\n=============================================", fg="cyan")
        click.secho(f"🚀 开始生成 第 {ch_idx} 章 ...", fg="cyan", bold=True)
        
        # 获取上一章的内容（如果有）作为连贯性参考
        prev_content = ""
        if ch_idx > 1:
            prev_file = os.path.join(project_root, "正文", f"第{volume_num}卷", f"第{ch_idx-1}章.md")
            # 简化起见，如果上一章在上一卷，这里忽略，实际应该跨卷寻找
            if os.path.exists(prev_file):
                with open(prev_file, 'r', encoding='utf-8') as f:
                    # 只取最后 1000 字作为上下文
                    content = f.read()
                    prev_content = content[-1000:] if len(content) > 1000 else content

        # --------------------------------------------------------------------------------
        # Agent 1: Drafting Agent (草稿起草)
        # --------------------------------------------------------------------------------
        click.secho(f"  [1/3] ✍️ Drafting Agent 正在起草...", fg="yellow")
        
        draft_sys_prompt = f"""
        你是一位顶级的网络小说白金作家。现在你需要根据提供的大纲和设定，撰写小说《{title}》的 第 {ch_idx} 章。
        
        【写作核心原则】：
        1. 严格遵循设定的世界观与力量体系，绝不能OOC（Character Out Of Character）。
        2. 每章字数要求在 2500 - 3500 字之间，必须有充分的细节描写（环境渲染、人物心理、动作场面）。
        3. 代入感强，符合网文爽文节奏，情绪要到位。
        4. 结尾必须卡在钩子处，留下悬念。
        
        【输出格式限定】：
        请直接输出小说正文内容，无需输出标题，无需任何分析解释。
        开头和结尾不要加任何 Markdown 代码块包裹，纯文本输出。
        """
        
        draft_user_prompt = f"""
        【项目设定库】
        {settings_context}
        
        【卷大纲】
        {volume_outline}
        
        【上一章结尾 (用于衔接)】
        {prev_content if prev_content else "(本卷第一章，无上一章内容)"}
        
        请严格根据卷大纲中关于 第 {ch_idx} 章 的剧情规划以及上一章结尾的衔接，撰写本章的正文草稿。
        """
        
        try:
            draft_content = llm.chat(prompt=draft_user_prompt, system_prompt=draft_sys_prompt)
        except Exception as e:
            click.secho(f"❌ 第 {ch_idx} 章起草失败: {e}", fg="red")
            break

        # --------------------------------------------------------------------------------
        # Agent 2: Review Agent (交叉审查)
        # --------------------------------------------------------------------------------
        click.secho(f"  [2/3] 🔍 Review Agent 正在毒点审查...", fg="blue")
        review_sys_prompt = """
        你是一个苛刻的网文总编。你的任务是审查由AI生成的初稿，找出可能存在的“毒点”、人物OOC、设定冲突或节奏拖沓的地方。
        请输出一份简短但尖锐的修改意见，列出至少 3 条需要改进的关键点。不要客套。
        """
        try:
            review_feedback = llm.chat(prompt=f"【当前章节草稿】：\n{draft_content}\n\n请针对上述草稿提出修改意见。", system_prompt=review_sys_prompt, max_tokens=1000)
            click.echo(f"  > 审查意见: {review_feedback[:100].replace(chr(10), ' ')}...")
        except Exception as e:
            click.secho(f"❌ 第 {ch_idx} 章审查失败，跳过审查: {e}", fg="red")
            review_feedback = "草稿质量尚可，无需大幅修改。"

        # --------------------------------------------------------------------------------
        # Agent 3: Polish Agent (精修润色)
        # --------------------------------------------------------------------------------
        click.secho(f"  [3/3] ✨ Polish Agent 正在终稿润色...", fg="magenta")
        polish_sys_prompt = """
        你是一位网文精修师。你将收到一份初稿和总编的修改意见。
        请根据总编的修改意见对文章进行大幅度润色。要求：
        1. 消除一切浓重的“AI翻译腔”和说教味。
        2. 全面应用修改意见中的建议。
        3. 加强对话的张力、动作描写的画面感。
        
        请直接输出最终的正文文本，不要包含任何前置解释和标题。
        """
        
        polish_user_prompt = f"""
        【初稿】：
        {draft_content}
        
        【修改意见】：
        {review_feedback}
        
        请查收并输出最终定稿。
        """
        
        try:
            final_content = llm.chat(prompt=polish_user_prompt, system_prompt=polish_sys_prompt)
        except Exception as e:
            click.secho(f"❌ 第 {ch_idx} 章润色失败: {e}", fg="red")
            break
            
        # 简单清理可能存在的 Markdown 格式
        final_content = final_content.strip()
        if final_content.startswith("```"):
            final_content = final_content.split("\n", 1)[-1]
        if final_content.endswith("```"):
            final_content = final_content.rsplit("\n", 1)[0]
            
        # --------------------------------------------------------------------------------
        # 保存与更新
        # --------------------------------------------------------------------------------
        # 自动提取标题 (如果LLM还是生成了的话)，如果没有则用占位符
        lines = [line.strip() for line in final_content.split('\n') if line.strip()]
        chapter_title = "未知章节"
        if lines and ("章" in lines[0][:20] or "第" in lines[0][:10]):
            chapter_title = lines[0]
            
        # 保存文件
        chapter_file_path = os.path.join(chapter_dir, f"第{ch_idx}章.md")
        with open(chapter_file_path, 'w', encoding='utf-8') as f:
            if not final_content.startswith("# "):
                f.write(f"# 第{ch_idx}章：自动生成草稿\n\n")
            f.write(final_content)
            
        click.secho(f"  ✅ 第 {ch_idx} 章写入成功！({len(final_content)} 字) -> {chapter_file_path}", fg="green")
        
        # 更新状态
        state["progress"]["current_chapter"] = ch_idx
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            
    click.secho(f"\n🎉 批量生成完毕！共完成 {write_count} 章。", fg="green", bold=True)
