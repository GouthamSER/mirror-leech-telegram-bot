from . import LOGGER, bot_loop
from .core.telegram_manager import TgClient
from .core.config_manager import Config
Config.load()

# ── Health-check server (Koyeb TCP check on $PORT / 8080) ──────────────────
import os
from aiohttp import web as _web

async def _health(_request):
    return _web.Response(text="OK")

async def _start_health_server():
    port = int(os.environ.get("PORT", 8080))
    app = _web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = _web.AppRunner(app)
    await runner.setup()
    site = _web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER.info(f"Health-check server listening on port {port}")
# ───────────────────────────────────────────────────────────────────────────

async def main():
    from asyncio import gather
    from .core.startup import (
        load_settings,
        load_configurations,
        save_settings,
        update_aria2_options,
        update_nzb_options,
        update_qb_options,
        update_variables,
    )

    # Start health-check server first so Koyeb sees port 8080 immediately
    await _start_health_server()

    await load_settings()
    await gather(TgClient.start_bot(), TgClient.start_user())
    await gather(load_configurations(), update_variables())
    from .core.torrent_manager import TorrentManager
    await TorrentManager.initiate()
    await gather(
        update_qb_options(),
        update_aria2_options(),
        update_nzb_options(),
    )
    from .helper.ext_utils.files_utils import clean_all
    from .core.jdownloader_booter import jdownloader
    from .helper.ext_utils.telegraph_helper import telegraph
    from .helper.mirror_leech_utils.rclone_utils.serve import rclone_serve_booter
    from .modules import (
        initiate_search_tools,
        get_packages_version,
        restart_notification,
    )
    await gather(
        save_settings(),
        jdownloader.boot(),
        clean_all(),
        initiate_search_tools(),
        get_packages_version(),
        restart_notification(),
        telegraph.create_account(),
        rclone_serve_booter(),
    )

bot_loop.run_until_complete(main())
from .helper.ext_utils.bot_utils import create_help_buttons
from .helper.listeners.aria2_listener import add_aria2_callbacks
from .core.handlers import add_handlers
add_aria2_callbacks()
create_help_buttons()
add_handlers()
LOGGER.info("Bot Started!")
bot_loop.run_forever()
