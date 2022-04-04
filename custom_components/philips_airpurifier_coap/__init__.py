"""Support for Philips AirPurifier with CoAP."""
from __future__ import annotations

import asyncio
import logging
from struct import pack

from aioairctrl import CoAPClient
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from .philips import PhilipsEntity, Coordinator

from .const import (
    CONF_MODEL,
    CONF_DEVICE_ID,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = ["fan", "sensor"]
PLATFORMS = ["fan"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Philips AirPurifier integration."""
    _LOGGER.debug("async_setup_entry called")

    host = entry.data[CONF_HOST]

    _LOGGER.debug("Setting up %s integration with %s", DOMAIN, host)

    try:
        client = await CoAPClient.create(host)
        _LOGGER.debug("got a valid client")
    except Exception as ex:
        _LOGGER.warning(r"Failed to connect: %s", ex)
        raise ConfigEntryNotReady from ex

    coordinator = Coordinator(client)
    _LOGGER.debug("got a valid coordinator")

    data = hass.data.get(DOMAIN)
    if data == None:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][host] = {
        DATA_KEY_CLIENT: client,
        DATA_KEY_COORDINATOR: coordinator,
    }

    await coordinator.async_first_refresh()
    _LOGGER.debug("coordinator did first refresh")

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)

    hass.data[DOMAIN].pop(entry.data[CONF_HOST])

    return True


# async def async_setup_old(hass: HomeAssistant, config: ConfigType) -> bool:
#     """Set up the Philips AirPurifier integration."""
#     hass.data[DOMAIN] = {}

#     async def async_setup_air_purifier(conf: ConfigType):
#         host = conf[CONF_HOST]

#         _LOGGER.debug("Setting up %s integration with %s", DOMAIN, host)

#         try:
#             client = await CoAPClient.create(host)
#         except Exception as ex:
#             _LOGGER.warning(r"Failed to connect: %s", ex)
#             raise ConfigEntryNotReady from ex

#         coordinator = Coordinator(client)

#         hass.data[DOMAIN][host] = {
#             DATA_KEY_CLIENT: client,
#             DATA_KEY_COORDINATOR: coordinator,
#         }

#         await coordinator.async_first_refresh()

#         # autodetect model and name
#         model = coordinator.status['type']
#         name = coordinator.status['name']
#         conf[CONF_MODEL] = model
#         conf[CONF_NAME] = name
#         _LOGGER.debug("Detected host %s as model %s with name: %s", host, model, name)

#         for platform in PLATFORMS:
#             hass.async_create_task(
#                 discovery.async_load_platform(hass, platform, DOMAIN, conf, config)
#             )

#     tasks = [async_setup_air_purifier(conf) for conf in config[DOMAIN]]
#     if tasks:
#         await asyncio.wait(tasks)

#     return True