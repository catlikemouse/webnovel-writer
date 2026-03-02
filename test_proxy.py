from anthropic import Anthropic

client = Anthropic(
    base_url="https://investments-organization-identifier-criterion.trycloudflare.com",
    api_key="sk-4f5fd675bb47490c87490af189cd222a"
)

try:
    response = client.messages.create(
        model="claude-opus-4-6-thinking",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("代理测试成功！AI 回复内容如下：\n")
    # claude-opus-4-6-thinking 会先返回 thinking block，再返回 text block
    text_content = next(block.text for block in response.content if block.type == 'text')
    print(text_content)
except Exception as e:
    print("代理测试失败，错误信息：\n")
    print(e)
