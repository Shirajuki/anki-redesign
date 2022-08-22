from aqt import QPalette, mw
from aqt.toolbar import Toolbar
from typing import List

# TopToolbar styling fix through height change by adding <br> tag
def redraw_toolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval("""
        while (document.body.querySelectorAll("br.toolbarFix").length > 1)
            document.body.querySelectorAll("br.toolbarFix")[0].remove();
        const br = document.createElement("br");
        br.className = "toolbarFix";
        document.body.appendChild(br);
    """)

    if 'Qt6' in QPalette.ColorRole.__module__:
        mw.toolbar.web.eval("""
            while (document.body.querySelectorAll("div.toolbarFix").length > 1)
                document.body.querySelectorAll("div.toolbarFix")[0].remove();
            const div = document.createElement("div");
            div.style.width = "5px";
            div.style.height = "10px";
            div.className = "toolbarFix";
            document.body.appendChild(div);
        """)
    # Auto adjust the height, then redraw the toolbar
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw()

def redraw_toolbar_legacy(links: List[str], _: Toolbar) -> None:
    # Utilizing the link hook, we inject <br/> tag through javascript
    inject_br = """
        <script>
            while (document.body.querySelectorAll("br.toolbarFix").length > 1)
                document.body.querySelectorAll("br.toolbarFix")[0].remove();
            const br = document.createElement("br");
            br.className = "toolbarFix";
            document.body.appendChild(br);
        </script>
    """
    mw.toolbar.web.setFixedHeight(60)
    links.append(inject_br)
    mw.toolbar.web.adjustHeightToFit()