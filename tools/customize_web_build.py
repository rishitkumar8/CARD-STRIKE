from pathlib import Path
import re


INDEX_PATH = Path("build/web/index.html")


CUSTOM_STYLE = """
        :root {
            --bg-top: #262b41;
            --bg-bottom: #161a2a;
            --panel: rgba(32, 36, 54, 0.78);
            --border: rgba(100, 175, 195, 0.34);
            --text: #d2d7e1;
            --muted: #a0a8b9;
            --accent: #8cc3d2;
            --gold: #d7c382;
            --shadow: 0 24px 80px rgba(8, 10, 16, 0.42);
        }

        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        #status {
            display: block;
            margin: 0;
            font-weight: 600;
            color: var(--text);
            letter-spacing: 0.04em;
        }

        #progress {
            width: min(420px, 72vw);
            height: 10px;
            appearance: none;
            border: none;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.1);
        }

        #progress::-webkit-progress-bar {
            background: rgba(255, 255, 255, 0.1);
        }

        #progress::-webkit-progress-value {
            background: linear-gradient(90deg, #8cc3d2 0%, #d7c382 100%);
        }

        #progress::-moz-progress-bar {
            background: linear-gradient(90deg, #8cc3d2 0%, #d7c382 100%);
        }

        div.emscripten {
            text-align: center;
        }

        div.emscripten_border,
        div.thick_border {
            border: none;
        }

        canvas.emscripten {
            border: 0;
            background: transparent;
            width: 100%;
            height: 100%;
            max-width: 100vw;
            max-height: 100vh;
            z-index: 5;
            padding: 0;
            margin: auto;
            position: absolute;
            inset: 0;
        }

        body {
            font-family: Georgia, "Times New Roman", serif;
            margin: 0;
            background:
                radial-gradient(circle at top, rgba(140, 195, 210, 0.16), transparent 30%),
                radial-gradient(circle at 20% 80%, rgba(215, 195, 130, 0.14), transparent 28%),
                linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
            color: var(--text);
        }

        #transfer {
            position: absolute;
            inset: 0;
            z-index: 12;
            display: grid;
            place-items: center;
            pointer-events: none;
            transition: opacity 220ms ease;
        }

        #transfer.hidden {
            display: none !important;
        }

        .loader-shell {
            width: min(560px, calc(100vw - 48px));
            padding: 34px 30px 28px;
            border-radius: 28px;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(40, 45, 67, 0.9) 0%, rgba(23, 27, 42, 0.92) 100%);
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
        }

        .loader-kicker {
            margin-bottom: 10px;
            font-size: 0.78rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: var(--accent);
        }

        .loader-title {
            margin: 0;
            font-size: clamp(2.3rem, 7vw, 4.3rem);
            line-height: 0.96;
            color: var(--gold);
            text-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
        }

        .loader-subtitle {
            margin: 12px 0 22px;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.5;
        }

        .loader-status {
            display: grid;
            gap: 14px;
        }

        #status {
            padding: 10px 14px;
            border-radius: 14px;
            background: rgba(140, 195, 210, 0.14);
            border: 1px solid rgba(140, 195, 210, 0.18);
            color: #eef4ff;
        }

        .loader-tip {
            margin-top: 16px;
            font-size: 0.95rem;
            color: var(--muted);
        }

        #pyconsole,
        .topright,
        .bottomright {
            display: none !important;
        }
"""


CUSTOM_TRANSFER = """
    <div id="transfer" align="center">
        <div class="loader-shell">
            <div class="loader-kicker">Browser Edition</div>
            <h1 class="loader-title">MARV Strike</h1>
            <p class="loader-subtitle">Elemental tactics. Draft smart. Strike harder.</p>
            <div class="loader-status">
                <div class="emscripten" id="status">Loading battlefield...</div>
                <div class="emscripten">
                    <progress value="0" max="100" id="progress"></progress>
                </div>
            </div>
            <div class="loader-tip">When prompted, click anywhere to enter the arena.</div>
        </div>
    </div>
"""


def main() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")

    html = html.replace("Loading Card Strike from marve-strike.apk", "Loading MARV Strike from marve-strike.apk")
    html = html.replace('Title   : Card Strike', 'Title   : MARV Strike')
    html = html.replace('<title>Card Strike</title>', '<title>MARV Strike</title>')
    html = html.replace('platform.document.body.style.background = "#7f7f7f"', 'platform.document.body.style.background = "#161a2a"')
    html = html.replace('prompt = fnt.render("Ready to start !", True, "blue")', 'prompt = fnt.render("Click anywhere to start MARV Strike", True, "white")')
    html = html.replace('prompt = fnt.render(f"Setting [{pkg}] up", True, "black")', 'prompt = fnt.render(f"Preparing {pkg}", True, "white")')
    html = html.replace('platform.window.transfer.hidden = true', 'platform.window.transfer.classList.add("hidden")')
    html = html.replace(
        '        console.log(__FILE__, "custom_postrun")\n',
        '        console.log(__FILE__, "custom_postrun")\n        transfer.classList.add("hidden")\n',
    )

    html = re.sub(r"<style>.*?</style>", f"<style>{CUSTOM_STYLE}\n    </style>", html, count=1, flags=re.S)
    html = re.sub(r'<div id="transfer".*?</div>\s*</div>', CUSTOM_TRANSFER, html, count=1, flags=re.S)

    INDEX_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
