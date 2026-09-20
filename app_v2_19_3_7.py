"""Tyler AI v2.19.3.7: copy controls for assistant messages."""

import app_v2_19_3_6 as v21936


v21936.base.VERSION = "2.19.3.7-assistant-copy-buttons"
v21936.base.VERSION_SHORT = "v2.19.3.7"

base = v21936.base
app = v21936.app
ENGINE = v21936.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21936.EXECUTOR


_COPY_BUTTON_CSS = r"""
.copy-button{
    display:block;
    margin:10px 0 0 auto;
    min-height:32px;
    padding:6px 11px;
    border:1px solid #345176;
    border-radius:9px;
    background:#0a1829;
    color:#b9c9dd;
    font:600 12px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    cursor:pointer;
    touch-action:manipulation;
}
.copy-button:hover,.copy-button:focus-visible{
    color:#fff;
    border-color:#4b78ad;
    outline:none;
}
.copy-button:active{transform:translateY(1px)}
.copy-button.copied{
    color:#bbf7d0;
    border-color:#238552;
    background:#0b2a1d;
}
"""


_COPY_BUTTON_JS = r"""
async function copyTylerText(text,button){
    let copied = false;
    try{
        if(navigator.clipboard && window.isSecureContext){
            await navigator.clipboard.writeText(String(text || ""));
            copied = true;
        }
    }catch(_){
        copied = false;
    }

    if(!copied){
        const helper = document.createElement("textarea");
        helper.value = String(text || "");
        helper.setAttribute("readonly","");
        helper.style.position = "fixed";
        helper.style.opacity = "0";
        helper.style.pointerEvents = "none";
        document.body.appendChild(helper);
        helper.select();
        helper.setSelectionRange(0,helper.value.length);
        try{
            copied = document.execCommand("copy");
        }catch(_){
            copied = false;
        }
        helper.remove();
    }

    button.textContent = copied ? "Copied ✓" : "Copy failed";
    button.classList.toggle("copied",copied);
    window.setTimeout(() => {
        button.textContent = "Copy";
        button.classList.remove("copied");
    },1400);
}

function attachCopyButton(bubble,text){
    if(!bubble || bubble.querySelector(":scope > .copy-button")){
        return;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-button";
    button.textContent = "Copy";
    button.setAttribute("aria-label","Copy Tyler AI response");
    button.addEventListener("click",() => copyTylerText(text,button));
    bubble.appendChild(button);
}

document.querySelectorAll(".row.assistant .bubble").forEach(bubble => {
    attachCopyButton(bubble,bubble.textContent.trim());
});
"""


def _install_copy_buttons(template):
    css_marker = ".assistant .bubble{"
    js_marker = "function scrollDown(){"
    append_marker = "    bubble.appendChild(\n        body\n    );"
    if any(marker not in template for marker in (css_marker, js_marker, append_marker)):
        raise RuntimeError(
            "Tyler chat template changed; assistant copy buttons were not applied."
        )
    template = template.replace(css_marker, _COPY_BUTTON_CSS + "\n" + css_marker, 1)
    template = template.replace(js_marker, _COPY_BUTTON_JS + "\n\n" + js_marker, 1)
    template = template.replace(
        append_marker,
        append_marker
        + '\n\n    if(who === "assistant"){\n'
        + "        attachCopyButton(bubble,text);\n"
        + "    }",
        1,
    )
    return template


base.CHAT_HTML = _install_copy_buttons(base.CHAT_HTML)


_PREVIOUS_STATUS = app.view_functions["status"]


def status_v21937():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    capabilities = data.setdefault("capabilities", [])
    if "assistant_message_copy_buttons" not in capabilities:
        capabilities.append("assistant_message_copy_buttons")
    return base.jsonify(data)


app.view_functions["status"] = status_v21937


_ORIGINAL_SAFE_SOURCE_FILES = v21936._safe_source_files_v21936


def _safe_source_files_v21937():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_7.py"]))


EXECUTOR.safe_source_files_fn = _safe_source_files_v21937


__all__ = list(v21936.__all__) + [
    "_install_copy_buttons",
    "_safe_source_files_v21937",
    "status_v21937",
]
