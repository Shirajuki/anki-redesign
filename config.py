from aqt import mw

def get_config() -> dict:
    config: dict = mw.addonManager.getConfig(__name__) or dict()
    ## Addon fix
    config['addon_more_overview_stats'] = True if config.get('addon_more_overview_stats', "false").lower() == "true" else False
    config['addon_recolor'] = True if config.get('addon_recolor', "false").lower() == "true" else False
    ## Customization
    config['primary_color'] = config.get('primary_color', "#0093d0")
    config['link_color'] = config.get('link_color', "#77ccff")
    config['font'] = config.get('font', "Segoe UI")
    config['font_size'] = int(config.get('font_size', "12"))
    return config

def write_config(config):
    for key in config.keys():
        if not isinstance(config[key], str):
            config[key] = str(config[key])
    mw.addonManager.writeConfig(__name__, config)

config = get_config()
