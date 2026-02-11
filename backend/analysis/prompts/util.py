from django.conf import settings
from string import Template

def read_prompt_text(filename: str) -> str:
    path = settings.BASE_DIR / "analysis" / "prompts" / filename
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    if not isinstance(txt, str):
        raise TypeError(f"prompt template must be str, got {type(txt)}")
    return txt

def render_prompt(filename: str, ctx: dict) -> str:
    """무조건 str 텍스트에 대해서만 Template 치환을 한 번만 수행."""
    txt = read_prompt_text(filename)
    return Template(txt).safe_substitute(**ctx)