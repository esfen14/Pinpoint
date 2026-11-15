"""Package for the Nagios object template files (*.cfg.tpl) used by
host_config_templates. This initialiser only imports discover_network; it holds no
template logic.
"""
from server.app.network_discovery.network_discovery import discover_network
