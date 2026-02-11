BUCKET_LABELS_KO = {
    "STOCKS_KR": "국내주식",
    "STOCKS_GLB": "해외주식",
    "BONDS_KR": "국내채권",
    "BONDS_GLB": "해외채권",
    "ALTERNATIVES": "대체투자",
    "FUNDS": "펀드(멀티자산)",
    "CASH": "현금성자산",
}

def labels_table_lines() -> str:
    # 프롬프트에 넣을 표 형태
    return "\n".join([f"{k} = {v}" for k, v in BUCKET_LABELS_KO.items()])

def localize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    out = text
    # 긴 코드부터 교체(부분치환 방지)
    for k, v in sorted(BUCKET_LABELS_KO.items(), key=lambda x: -len(x[0])):
        out = out.replace(k, v)
    return out