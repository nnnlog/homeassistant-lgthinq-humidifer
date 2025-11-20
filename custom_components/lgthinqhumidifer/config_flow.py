"""Config flow for LG ThinQ Humidifier integration."""

import logging
import hashlib
import uuid
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .api import LGThinQAPI

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("refresh_token"): str,
    }
)


def generate_client_id():
    """Generate a random client ID hashed with SHA256."""
    random_uuid = str(uuid.uuid4())
    return hashlib.sha256(random_uuid.encode()).hexdigest()


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)

    # Generate client IDs if not present (though they should be passed in data for final entry)
    # But for validation, we need to use the ones we just generated or are about to use.
    # Wait, validate_input is called before entry creation.
    # We should generate IDs here or in async_step_user and pass them to API.

    client_id_mobile = data.get("client_id_mobile")
    client_id_web = data.get("client_id_web")

    api = LGThinQAPI(
        session,
        refresh_token=data["refresh_token"],
        client_id_mobile=client_id_mobile,
        client_id_web=client_id_web,
    )

    try:
        await api.async_login()
    except Exception as e:
        _LOGGER.error("Failed to login: %s", e)
        raise InvalidAuth

    return {"title": "LG ThinQ Humidifier"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LG ThinQ Humidifier."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Generate Client IDs
                client_id_mobile = generate_client_id()
                client_id_web = generate_client_id()

                user_input["client_id_mobile"] = client_id_mobile
                user_input["client_id_web"] = client_id_web

                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
