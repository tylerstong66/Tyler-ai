"""Tyler AI v2.19.3.4: accurate health checkpoints and safe Markdown UI."""

import app_v2_19_3_3 as v21933


v21933.base.VERSION = "2.19.3.4-operation-health-markdown-ui"
v21933.base.VERSION_SHORT = "v2.19.3.4"

base = v21933.base
app = v21933.app
ENGINE = v21933.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21933.EXECUTOR


_MARKDOWN_CSS = r"""
.assistant .message-body{white-space:normal}
.message-body>*:first-child{margin-top:0}
.message-body>*:last-child{margin-bottom:0}
.message-body p{margin:.6em 0;white-space:pre-wrap}
.message-body h1,.message-body h2,.message-body h3{margin:.8em 0 .35em;line-height:1.25}
.message-body h1{font-size:1.35em}.message-body h2{font-size:1.2em}.message-body h3{font-size:1.08em}
.message-body ul,.message-body ol{margin:.55em 0;padding-left:1.45em}
.message-body li{margin:.22em 0}
.message-body code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#071321;border:1px solid #223955;border-radius:5px;padding:.08em .3em;font-size:.9em}
.message-body pre{overflow-x:auto;margin:.7em 0;padding:11px 12px;background:#071321;border:1px solid #223955;border-radius:10px;white-space:pre}
.message-body pre code{border:0;padding:0;background:transparent;white-space:pre}
.message-body table{display:block;max-width:100%;overflow-x:auto;border-collapse:collapse;margin:.75em 0;font-size:.92em}
.message-body th,.message-body td{border:1px solid #2a4160;padding:7px 9px;text-align:left;vertical-align:top}
.message-body th{background:#10233a;color:#fff}
.message-body hr{border:0;border-top:1px solid #2a4160;margin:1em 0}
"""


_MARKDOWN_JS = r"""
function appendInlineMarkdown(parent,text){
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let cursor = 0;
    let match;
    while((match = pattern.exec(text)) !== null){
        if(match.index > cursor){
            parent.appendChild(document.createTextNode(text.slice(cursor,match.index)));
        }
        const token = match[0];
        const node = document.createElement(token.startsWith("**") ? "strong" : "code");
        node.textContent = token.startsWith("**") ? token.slice(2,-2) : token.slice(1,-1);
        parent.appendChild(node);
        cursor = match.index + token.length;
    }
    if(cursor < text.length){
        parent.appendChild(document.createTextNode(text.slice(cursor)));
    }
}

function tableCells(line){
    let value = line.trim();
    if(value.startsWith("|")){value = value.slice(1);}
    if(value.endsWith("|")){value = value.slice(0,-1);}
    return value.split("|").map(cell => cell.trim());
}

function isTableDivider(line){
    const cells = tableCells(line);
    return cells.length > 0 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
}

function renderMarkdown(parent,text){
    parent.className = "message-body";
    const lines = String(text || "").replace(/\r\n?/g,"\n").split("\n");
    let index = 0;
    while(index < lines.length){
        const line = lines[index];
        const trimmed = line.trim();
        if(!trimmed){index += 1;continue;}

        if(trimmed.startsWith("```")){
            const codeLines = [];
            index += 1;
            while(index < lines.length && !lines[index].trim().startsWith("```")){
                codeLines.push(lines[index]);
                index += 1;
            }
            if(index < lines.length){index += 1;}
            const pre = document.createElement("pre");
            const code = document.createElement("code");
            code.textContent = codeLines.join("\n");
            pre.appendChild(code);
            parent.appendChild(pre);
            continue;
        }

        const heading = /^(#{1,3})\s+(.+)$/.exec(trimmed);
        if(heading){
            const node = document.createElement("h" + heading[1].length);
            appendInlineMarkdown(node,heading[2]);
            parent.appendChild(node);
            index += 1;
            continue;
        }

        if(/^(-{3,}|\*{3,})$/.test(trimmed)){
            parent.appendChild(document.createElement("hr"));
            index += 1;
            continue;
        }

        if(line.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1])){
            const table = document.createElement("table");
            const thead = document.createElement("thead");
            const headerRow = document.createElement("tr");
            tableCells(line).forEach(value => {
                const th = document.createElement("th");
                appendInlineMarkdown(th,value);
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            const tbody = document.createElement("tbody");
            index += 2;
            while(index < lines.length && lines[index].includes("|") && lines[index].trim()){
                const row = document.createElement("tr");
                tableCells(lines[index]).forEach(value => {
                    const td = document.createElement("td");
                    appendInlineMarkdown(td,value);
                    row.appendChild(td);
                });
                tbody.appendChild(row);
                index += 1;
            }
            table.appendChild(tbody);
            parent.appendChild(table);
            continue;
        }

        const unordered = /^[-*+]\s+(.+)$/.exec(trimmed);
        const ordered = /^\d+[.)]\s+(.+)$/.exec(trimmed);
        if(unordered || ordered){
            const list = document.createElement(ordered ? "ol" : "ul");
            while(index < lines.length){
                const value = lines[index].trim();
                const itemMatch = ordered ? /^\d+[.)]\s+(.+)$/.exec(value) : /^[-*+]\s+(.+)$/.exec(value);
                if(!itemMatch){break;}
                const li = document.createElement("li");
                appendInlineMarkdown(li,itemMatch[1]);
                list.appendChild(li);
                index += 1;
            }
            parent.appendChild(list);
            continue;
        }

        const paragraph = document.createElement("p");
        appendInlineMarkdown(paragraph,line);
        parent.appendChild(paragraph);
        index += 1;
    }
}
"""


def _install_markdown_ui(template):
    css_marker = ".assistant .bubble{"
    js_marker = "function addMessage(\n    text,\n    who,\n    meta\n){"
    text_marker = "    body.textContent =\n        text;"
    if css_marker not in template or js_marker not in template or text_marker not in template:
        raise RuntimeError("Tyler chat template changed; safe Markdown UI patch was not applied.")
    template = template.replace(css_marker, _MARKDOWN_CSS + "\n" + css_marker, 1)
    template = template.replace(js_marker, _MARKDOWN_JS + "\n\n" + js_marker, 1)
    template = template.replace(
        text_marker,
        '    if(who === "assistant"){\n'
        '        renderMarkdown(body,text);\n'
        '    }else{\n'
        '        body.textContent = text;\n'
        '    }',
        1,
    )
    return template


base.CHAT_HTML = _install_markdown_ui(base.CHAT_HTML)


_PREVIOUS_STATUS = app.view_functions["status"]


def status_v21934():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    capabilities = data.setdefault("capabilities", [])
    for item in ["operation_checkpoint_health_history", "safe_markdown_chat_ui"]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21934


_ORIGINAL_SAFE_SOURCE_FILES = v21933._safe_source_files_v21933


def _safe_source_files_v21934():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_4.py"]))


v21933.v21932.v21931.v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21934
EXECUTOR.safe_source_files_fn = _safe_source_files_v21934


__all__ = list(v21933.__all__) + [
    "_install_markdown_ui", "_safe_source_files_v21934", "status_v21934"
]
